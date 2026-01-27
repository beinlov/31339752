-- ============================================================
-- 数据库外键约束修复脚本（精确版）
-- 目的：将 ON DELETE CASCADE 改为 ON DELETE RESTRICT
-- ============================================================
USE botnet;

-- 修复 botnet_communications_444
ALTER TABLE botnet_communications_444 
DROP FOREIGN KEY botnet_communications_444_ibfk_1;

ALTER TABLE botnet_communications_444 
ADD CONSTRAINT fk_node_444 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_444(id) ON DELETE RESTRICT;

-- 修复 botnet_communications_88888
ALTER TABLE botnet_communications_88888 
DROP FOREIGN KEY botnet_communications_88888_ibfk_1;

ALTER TABLE botnet_communications_88888 
ADD CONSTRAINT fk_node_88888 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_88888(id) ON DELETE RESTRICT;

-- 修复 botnet_communications_autoupdate
ALTER TABLE botnet_communications_autoupdate 
DROP FOREIGN KEY botnet_communications_autoupdate_ibfk_1;

ALTER TABLE botnet_communications_autoupdate 
ADD CONSTRAINT fk_node_autoupdate 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_autoupdate(id) ON DELETE RESTRICT;

-- 修复 botnet_communications_test
ALTER TABLE botnet_communications_test 
DROP FOREIGN KEY botnet_communications_test_ibfk_1;

ALTER TABLE botnet_communications_test 
ADD CONSTRAINT fk_node_test 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_test(id) ON DELETE RESTRICT;

-- 修复 botnet_communications_test222
ALTER TABLE botnet_communications_test222 
DROP FOREIGN KEY botnet_communications_test222_ibfk_1;

ALTER TABLE botnet_communications_test222 
ADD CONSTRAINT fk_node_test222 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_test222(id) ON DELETE RESTRICT;

-- 修复 botnet_communications_test333
ALTER TABLE botnet_communications_test333 
DROP FOREIGN KEY botnet_communications_test333_ibfk_1;

ALTER TABLE botnet_communications_test333 
ADD CONSTRAINT fk_node_test333 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_test333(id) ON DELETE RESTRICT;

-- 修复 botnet_communications_test444
ALTER TABLE botnet_communications_test444 
DROP FOREIGN KEY botnet_communications_test444_ibfk_1;

ALTER TABLE botnet_communications_test444 
ADD CONSTRAINT fk_node_test444 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_test444(id) ON DELETE RESTRICT;

SELECT 'Foreign key constraints updated successfully!' AS status;
