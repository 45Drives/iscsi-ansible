EVERYTHING YOU SHOULD NEED TO BUILD A HA ISCSI PCS CLUSTER WITH SCST


Start from scratch –
First things first, make sure target and targetcli are NOT installed. 
dnf remove targetcli target

Step 1: (CLUSTER SETUP)
Passwordless ssh between both nodes (not necessary but good to have)
Ensure each gateway has a hostname entry for themselves and partner in /etc/hosts
All hosts: Enable Rocky-Highavailability repo
vim /etc/yum.repos.d/Rocky-HighAvailability.repo and set enabled=1 
All hosts: update repo cache
 dnf makecache
All hosts: open all required ports on firewalld firewall – pacemaker/corosync/iSCSI 
firewall-cmd –permanent –add-service=high-availability
firewall-cmd –permanent –add-port=3260/tcp 
firewall-cmd --reload 
All hosts: Install pcs pacemaker corosync and enable 
dnf install pcs pacemaker corosync ceph-resource-agents -y
systemctl enable --now pcsd
All hosts: Set the password for the hauser the same for all hosts 
passwd hacluster 
From HOST1: Authorize both nodes for the cluster
pcs host auth <NODE1> <NODE2> -u hacluster -p password
FROM HOST1: Create the cluster: 
pcs cluster setup <CLUSTERNAME> <HOSTNAME1> <HOSTNAME2> --start –enable
Check status: pcs status – we should have an active cluster with no resources
If PCS ever has errors – when in doubt run the command “pcs resource cleanup” 

Step 2: (ISCSI SERVICE SETUP)
All hosts: Install SCST: 
dnf group install “development tools”
dnf install -y kernel-devel perl perl-Data-Dumper perl-ExtUtils-MakeMaker rpm-build dkms git
now we git clone scst so we can compile rpms
git clone https://github.com/SCST-project/scst
# cd scst/
# make rpm-dkms
# cd ~/
# dnf install -y /usr/src/packages/RPMS/x86_64/scst*
Boom – should have everything installed ready to go now.
Next step clear scst.conf
echo -n "" > /etc/modules-load.d/scst.conf
Next, enable the kernel module 
for i in iscsi-scst scst scst_vdisk; do echo $i >> /etc/modules-load.d/scst.conf && modprobe $i ; done
This will load the kernel modules for SCST. To ensure they’re loaded run the command “lsmod” and check to ensure you see:
scst_vdisk            135168  0
iscsi_scst            126976  0
scst                 3641344  2 scst_vdisk,iscsi_scst

Next, we must create a systemd service to start iscsi-scst  and enable it.
Create a new file:
vim /etc/systemd/system/iscsi-scst.service
Inside the file add these lines:
[Unit]
Description=iSCSI SCST Target Daemon
Documentation=man:iscsi-scstd(8)
After=network.target
Before=scst.service
Conflicts=shutdown.target
[Service]
EnvironmentFile=-/etc/sysconfig/scst
PIDFile=/var/run/iscsi-scstd.pid
ExecStartPre=/sbin/modprobe iscsi-scst
ExecStart=/sbin/iscsi-scstd $ISCSID_OPTIONS
[Install]
WantedBy=multi-user.target

Next, enable and start the service.
systemctl daemon-reload 
systemctl enable –now iscsi-scst

One last note that everything so far is to be completed on ALL nodes. 

Step 3:
 – Create N number of RBDs you’re going to use for your iSCSI configuration that will be made into the VG/LV. Do this however you prefer, through the Ceph dashboard or CLI.
Step 4
All hosts:  – Set up lvm.conf and lvmlocal.conf to configure clustering:
Step 4.A 
All hosts: open /etc/lvm/lvm.conf find “system_id_source” line (it should be line 1356). Uncomment this line and set it to:
system_id_source = “lvmlocal”
Next, find the line “types”. (It should be line 201) Uncomment it and set it to:
types = [ "rbd", 1024 ]
Step 4.B
All hosts:  open /etc/lvm/lvmlocal.conf  and find “system_id = “ line. Uncomment this line and set it to:
system_id = “iscsilun”
All commands from here on are only to be run from a single host. Step 5 – 9 are all used to prep the RBDs which needs to be done from a single host, and then steps 10 – 12 are all PCS cluster commands which means by design, they only need to be run once and it will take effect for the entire cluster
Step 5:
 One host: – Map all RBDs to your host temporarily
rbd map rbd/<RBDNAME>
Step 6
 – Create the PV/VG out of the RBDs mapped from previous step
pvcreate /dev/rbdX  pvcreate /dev/rbdX ….etc
vgcreate <VGNAME> <PV1> <PV2> <PV…>
Step 7
 – Create LV with stripe: lvcreate -i <NUMBER_OF_RBDS> -I 64 -l 100%FREE -n <LVNAME> <VGNAME> /dev/rbdX /dev/rbdX /dev/rbdN 
Step 8
 – deactivate the LV: 
lvchange -an VGNAME/LVNAME
Step 9
 – Unmount the RBDs from the host
rbd unmap /dev/rbdX rbd unamp /dev/rbdX …etc
Step 10
 – Set both nodes to standby
pcs node standby <node1> <node2>
Step 11
 – Begin creating resources


RBD resource:
pcs resource create <RBDRESOURCENAME> ocf:ceph:rbd name=<RBDNAME> pool=<POOLNAME> user=admin cephconf=/etc/ceph/ceph.conf op start timeout=60s interval=0 op stop timeout=60s interval=0 op monitor timeout=30s interval=15s


VIP resource (one for each VIP):
pcs resource create <VIPRESOURCNEAME> ocf:heartbeat:IPaddr2 ip=xxx.xxx.xxx.xxx cidr_netmask=xx op start timeout=20 op stop timeout=20 op monitor interval=10

iSCSITarget resource:
pcs resource create <ISCSITARGETRESOURCENAME> ocf:heartbeat:iSCSITarget iqn=iqn.xxxx-xx.com.45drives:iscsi portals=xxx.xxx.xxx.xxx:3260 op start timeout=20 op stop timeout=20 op monitor interval=20 timeout=40

iSCSILUN resource (one for each RBD):
pcs resource create <ISCSILUNRESOURCENAME> ocf:heartbeat:iSCSILogicalUnit target_iqn=iqn.xxxx-xx.com.45drives:iscsi lun=0 path=/dev/rbdXX op start timeout=100 op stop timeout=100 op monitor interval=10 timeout=100

iSCSI port block resources (on/off): 
pcs resource create <PORTBLOCK_ON_RESOURCNEAME> ocf:heartbeat:portblock ip=PORTALIP portno=3260 protocol=tcp action=block op start timeout=20 op stop timeout=20 op monitor timeout=20 interval=20
pcs resource create <PORTBLOCK_OFF_RESOURCNEAME> ocf:heartbeat:portblock ip=PORTALIP portno=3260 protocol=tcp action=unblock op start timeout=20 op stop timeout=20 op monitor timeout=20 interval=20

LVM resource:
pcs resource create<LVMRESOURCE_NAME> ocf:heartbeat:LVM-activate lvname=<LVNAME> vgname=<VGNAME> activation_mode=exclusive vg_access_mode=system_id op start timeout=30 op stop timeout=30 op monitor interval=10 timeout=60

All resources are now created. 
Step 12: 
-Create PCS group and constraints for order and colocation.
The order you create the group in is VERY IMPORTANT. The order of the resources given during group creation is the order that the resources will start and stop in the cluster. 

PCS Resource group (USE THE SAME ORDER): 
pcs resource group add <GROUP_NAME> <PORTBLOCK_ON_RESOURCE> <ISCSI_VIP_RESOURCE> <LVM_RESOURCE> <ISCSI_TARGET_RESOURCE> <iSCSI_LUN_RESOURCE> <PORTBLOCK_OFF_RESOURCE>

Finally, add constraints to say that the RBD resources will always live on the same node as the resource group, and also add constraints to say that the RBDs have to always be up before the group tries to activate anything.
These 2 commands must be run for EVERY SINGLE RBD resource:
pcs constraint colocation add <RBDRESOURCE> with <RESOURCE_GROUP> INFINITY
 pcs constraint order start <RBDRESOURCE> then <RESOURCE_GROUP> 
 




Flow for the playbook:
    • Enable Rocky-HA repo
    • Update cache
    • Install scst, pcs, pacemaker, corosync, ceph-common, ceph-resource-agents
    • Modprobe iscsi-scst scst scst_vdisk
    • echo the following lines into /etc/modules-load.d/scst.conf:
        ◦ iscsi-scst
        ◦ scst
        ◦ scst_vdisk
    • enable and start pcsd service
    • Move our custom iSCSITarget and iSCSILogicalUnit files into /usr/lib/ocf/resource.d/heartbeat/
    • set password for hacluster user to anything as long as it matches on both nodes. 
    • authorize nodes and create cluster
    • open all PCS firewall ports and port 3260/tcp for iSCSI

Next, we branch off into possible scenarios.


If the user is making use of LVM and specifically LVM striping in their LUNs, these are the next steps:
    • Set LVM configurations necessary in /etc/lvm/lvm.conf :
        ◦ types = [ “rbd” , 1024 ]
        ◦ system_id_source = “lvmlocal”
    • Set LVM configurations necessary in /etc/lvm/lvmlocal.conf
        ◦ system_id = “iscsilun”
    • mount the rbds given in the all.yml file on any one host
    • create pvs for each
    • create vg with the vgname provided in all.yml
    • create lv with lvname provided in all.yml using the following command:
        ◦ lvcreate -i 4 -I 64 -l 100%FREE -n LVNAME VGNAME /dev/rbdX /dev/rbdX /dev/rbdX /dev/rbdX
    • deactivate lv: lvchange -an lvname
    • unmount rbds
    • Create RBD resources – one for each:
        ◦ pcs resource create <RBDRESOURCENAME> ocf:ceph:rbd name=<RBDNAME> pool=<POOLNAME> user=admin cephconf=/etc/ceph/ceph.conf op start timeout=100 interval=10 op stop timeout=100 interval=10 op monitor timeout=100 interval=10

    • Create VIP resource – Could be one or two depending on if they wish to use MPIO
        ◦ pcs resource create <VIPRESOURCNEAME> ocf:heartbeat:IPaddr2 ip=xxx.xxx.xxx.xxx cidr_netmask=xx op start timeout=20 op stop timeout=20 op monitor interval=10

    • Create iSCSI Target resource – If they specify one portal you use one, otherwise the way you separate multiple portals in this command is by using quotations and just a space between each portal. For example, portals=”10.10.10.1:3260 10.10.20.1:3260” will write the conf properly
    • There is always a relationship of One Vip per one portal
        ◦ pcs resource create <ISCSITARGETRESOURCENAME> ocf:heartbeat:iSCSITarget iqn=iqn.xxxx-xx.com.45drives:iscsi portals=xxx.xxx.xxx.xxx:3260 op start timeout=20 op stop timeout=20 op monitor interval=20 timeout=40

    • Create iSCSI LUN resource – There will be one for each LV
        ◦ pcs resource create <ISCSILUNRESOURCENAME> ocf:heartbeat:iSCSILogicalUnit target_iqn=iqn.xxxx-xx.com.45drives:iscsi lun=0 path=/dev/rbdXX op start timeout=100 op stop timeout=100 op monitor interval=10 timeout=100

    • Create Portblock ON resource – 
        ◦ pcs resource create <PORTBLOCK_ON_RESOURCNEAME> ocf:heartbeat:portblock ip=PORTALIP portno=3260 protocol=tcp action=block op start timeout=20 op stop timeout=20 op monitor timeout=20 interval=20

    • Create Portblock OFF resource –
        ◦ pcs resource create <PORTBLOCK_OFF_RESOURCNEAME> ocf:heartbeat:portblock ip=PORTALIP portno=3260 protocol=tcp action=unblock op start timeout=20 op stop timeout=20 op monitor timeout=20 interval=20



    • Create PCS group to group a number of resources together – the order they are added in matters greatly. The order is as follows:
        ◦ pcs resource group add <GROUP_NAME> <PORTBLOCK_ON_RESOURCE> <ISCSI_VIP_RESOURCE> <LVM_RESOURCE> <ISCSI_TARGET_RESOURCE> <iSCSI_LUN_RESOURCE> <PORTBLOCK_OFF_RESOURCE>

    • Create PCS constraints – one for each RBD
        ◦ pcs constraint colocation add <RBDRESOURCE> with <RESOURCE_GROUP> INFINITY
        ◦ pcs constraint order start <RBDRESOURCE> then <RESOURCE_GROUP> 

    • run a pcs resource cleanup to bring everything up healthy


Next scenario – User did not include any LVM and is just using one or more RBDs they wish to use as iSCSI LUNS:

    • Create RBD resources – one for each:
        ◦ pcs resource create <RBDRESOURCENAME> ocf:ceph:rbd name=<RBDNAME> pool=<POOLNAME> user=admin cephconf=/etc/ceph/ceph.conf op start timeout=100 interval=10 op stop timeout=100 interval=10 op monitor timeout=100 interval=10

    • Create VIP resource – Could be one or two depending on if they wish to use MPIO
        ◦ pcs resource create <VIPRESOURCNEAME> ocf:heartbeat:IPaddr2 ip=xxx.xxx.xxx.xxx cidr_netmask=xx op start timeout=20 op stop timeout=20 op monitor interval=10

    • Create iSCSI Target resource – If they specify one portal you use one, otherwise the way you separate multiple portals in this command is by using quotations and just a space between each portal. For example, portals=”10.10.10.1:3260 10.10.20.1:3260” will write the conf properly
        ◦ pcs resource create <ISCSITARGETRESOURCENAME> ocf:heartbeat:iSCSITarget iqn=iqn.xxxx-xx.com.45drives:iscsi portals=xxx.xxx.xxx.xxx:3260 op start timeout=20 op stop timeout=20 op monitor interval=20 timeout=40

    • Create iSCSI LUN resource – There will be one for each RBD
        ◦ pcs resource create <ISCSILUNRESOURCENAME> ocf:heartbeat:iSCSILogicalUnit target_iqn=iqn.xxxx-xx.com.45drives:iscsi lun=0 path=/dev/rbdXX op start timeout=100 op stop timeout=100 op monitor interval=10 timeout=100

    • Create Portblock ON resource – 
        ◦ pcs resource create <PORTBLOCK_ON_RESOURCNEAME> ocf:heartbeat:portblock ip=PORTALIP portno=3260 protocol=tcp action=block op start timeout=20 op stop timeout=20 op monitor timeout=20 interval=20

    • Create Portblock OFF resource –
        ◦ pcs resource create <PORTBLOCK_OFF_RESOURCNEAME> ocf:heartbeat:portblock ip=PORTALIP portno=3260 protocol=tcp action=unblock op start timeout=20 op stop timeout=20 op monitor timeout=20 interval=20



    • Create PCS group to group a number of resources together – the order they are added in matters greatly. The order is as follows:
        ◦ pcs resource group add <GROUP_NAME> <PORTBLOCK_ON_RESOURCE> <ISCSI_VIP_RESOURCE> <LVM_RESOURCE> <ISCSI_TARGET_RESOURCE> <iSCSI_LUN_RESOURCE> <PORTBLOCK_OFF_RESOURCE>

    • Create PCS constraints – one for each RBD
        ◦ pcs constraint colocation add <RBDRESOURCE> with <RESOURCE_GROUP> INFINITY
        ◦ pcs constraint order start <RBDRESOURCE> then <RESOURCE_GROUP> 

    • run a pcs resource cleanup to bring everything up healthy


Additional safety measures – This is best used if the gateways are being used as iSCSI servers *only* and don’t have other clustered solutions on them (CTDB, HA-NFS, RGW, etc)

Create IPMI fencing stonith resources:
pcs stonith create <FENCINGNAME>  fence_ipmilan ip=<IPMIADDRESS> username=<IPMIUSER> password=<IPMIPASSWORD> lanplus=1 pcmk_host_list=<GW_HOSTNAME>
Repeat for the other gateway host(s)

Once all stonith resources are created, re-enable fencing:
pcs property set stonith-enabled=false

pcs resource cleanup
pcs stonith cleanup
