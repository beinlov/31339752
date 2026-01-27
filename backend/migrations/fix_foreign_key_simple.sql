-- ============================================================
-- 数据库外键约束修复脚本（简化版）
-- ============================================================
USE botnet;

-- 2.1 asruex
ALTER TABLE botnet_communications_asruex DROP FOREIGN KEY IF EXISTS fk_node_asruex;
ALTER TABLE botnet_communications_asruex 
ADD CONSTRAINT fk_node_asruex 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_asruex(id) ON DELETE RESTRICT;

-- 2.2 mozi
ALTER TABLE botnet_communications_mozi DROP FOREIGN KEY IF EXISTS fk_node_mozi;
ALTER TABLE botnet_communications_mozi 
ADD CONSTRAINT fk_node_mozi 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_mozi(id) ON DELETE RESTRICT;

-- 2.3 andromeda
ALTER TABLE botnet_communications_andromeda DROP FOREIGN KEY IF EXISTS fk_node_andromeda;
ALTER TABLE botnet_communications_andromeda 
ADD CONSTRAINT fk_node_andromeda 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_andromeda(id) ON DELETE RESTRICT;

-- 2.4 moobot
ALTER TABLE botnet_communications_moobot DROP FOREIGN KEY IF EXISTS fk_node_moobot;
ALTER TABLE botnet_communications_moobot 
ADD CONSTRAINT fk_node_moobot 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_moobot(id) ON DELETE RESTRICT;

-- 2.5 ramnit
ALTER TABLE botnet_communications_ramnit DROP FOREIGN KEY IF EXISTS fk_node_ramnit;
ALTER TABLE botnet_communications_ramnit 
ADD CONSTRAINT fk_node_ramnit 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_ramnit(id) ON DELETE RESTRICT;

-- 2.6 leethozer
ALTER TABLE botnet_communications_leethozer DROP FOREIGN KEY IF EXISTS fk_node_leethozer;
ALTER TABLE botnet_communications_leethozer 
ADD CONSTRAINT fk_node_leethozer 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_leethozer(id) ON DELETE RESTRICT;

-- 2.7 test
ALTER TABLE botnet_communications_test DROP FOREIGN KEY IF EXISTS fk_node_test;
ALTER TABLE botnet_communications_test 
ADD CONSTRAINT fk_node_test 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_test(id) ON DELETE RESTRICT;

SELECT '外键约束修改完成！' AS status;
