ALTER TABLE ESX_CLUSTER RENAME COLUMN "VM_TO_HOST_RATIO" to "VM_COUNT";

ALTER TABLE ESX_CLUSTER ADD HOST_COUNT NUMBER(*,0);

UPDATE ESX_CLUSTER SET HOST_COUNT = 1;
ALTER TABLE ESX_CLUSTER MODIFY HOST_COUNT NOT NULL;

commit;