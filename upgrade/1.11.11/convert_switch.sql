RENAME switch TO network_device;
UPDATE hardware_entity SET hardware_type = 'network_device' WHERE hardware_type = 'switch';
ALTER TABLE network_device RENAME CONSTRAINT SWITCH_HW_ENT_ID_NN TO NETWORK_DEVICE_HW_ENT_ID_NN;
ALTER TABLE network_device RENAME CONSTRAINT SWITCH_LAST_POLL_NN TO NETWORK_DEVICE_LAST_POLL_NN;
ALTER TABLE network_device RENAME CONSTRAINT SWITCH_SWITCH_TYPE_NN TO NETWORK_DEVICE_SWITCH_TYPE_NN;
ALTER TABLE network_device RENAME CONSTRAINT SWITCH_PK TO NETWORK_DEVICE_PK;
ALTER TABLE network_device RENAME CONSTRAINT SWITCH_HW_ENT_FK TO NETWORK_DEVICE_HW_ENT_FK;

ALTER TABLE esx_cluster RENAME COLUMN switch_id TO network_device_id;
ALTER TABLE esx_cluster DROP CONSTRAINT "ESX_CLUSTER_SWITCH_FK";
ALTER TABLE esx_cluster ADD CONSTRAINT "ESX_CLUSTER_NETWORK_DEVICE_FK"
	FOREIGN KEY ("NETWORK_DEVICE_ID")
	REFERENCES "NETWORK_DEVICE" ("HARDWARE_ENTITY_ID")
	ENABLE;

ALTER TABLE observed_mac RENAME COLUMN switch_id TO network_device_id;
ALTER TABLE observed_mac RENAME CONSTRAINT OBSERVED_MAC_SWITCH_ID_NN TO OBSERVED_MAC_NETDEV_ID_NN;

ALTER TABLE observed_vlan RENAME COLUMN switch_id TO network_device_id;
ALTER TABLE observed_vlan RENAME CONSTRAINT OBSERVED_VLAN_SWITCH_ID_NN TO OBSERVED_VLAN_NETDEV_ID_NN;

ALTER INDEX "ESX_CLUSTER_SWITCH_IDX" RENAME TO "ESX_CLUSTER_NETWORK_DEVICE_IDX";
ALTER INDEX "SWITCH_PK" RENAME TO "NETWORK_DEVICE_PK";

QUIT;