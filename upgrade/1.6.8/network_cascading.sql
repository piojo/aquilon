ALTER TABLE system DROP CONSTRAINT "SYSTEM_NET_ID_FK";
ALTER TABLE system ADD CONSTRAINT "SYSTEM_NET_ID_FK" FOREIGN KEY (network_id) REFERENCES network (id) ON DELETE SET NULL;