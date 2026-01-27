-- ============================================================
-- 为缺少外键的通信表添加外键约束
-- ============================================================
USE botnet;

-- andromeda
ALTER TABLE botnet_communications_andromeda 
ADD CONSTRAINT fk_node_andromeda 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_andromeda(id) ON DELETE RESTRICT;

-- asruex
ALTER TABLE botnet_communications_asruex 
ADD CONSTRAINT fk_node_asruex 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_asruex(id) ON DELETE RESTRICT;

-- leethozer
ALTER TABLE botnet_communications_leethozer 
ADD CONSTRAINT fk_node_leethozer 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_leethozer(id) ON DELETE RESTRICT;

-- moobot
ALTER TABLE botnet_communications_moobot 
ADD CONSTRAINT fk_node_moobot 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_moobot(id) ON DELETE RESTRICT;

-- mozi
ALTER TABLE botnet_communications_mozi 
ADD CONSTRAINT fk_node_mozi 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_mozi(id) ON DELETE RESTRICT;

-- ramnit
ALTER TABLE botnet_communications_ramnit 
ADD CONSTRAINT fk_node_ramnit 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_ramnit(id) ON DELETE RESTRICT;

SELECT 'Missing foreign keys added successfully!' AS status;
