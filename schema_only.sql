-- 数据库建表脚本
-- 自动从botnet.sql提取

USE botnet;
SET FOREIGN_KEY_CHECKS = 0;
SET NAMES utf8mb4;

DROP TABLE IF EXISTS `anomaly_reports`;

CREATE TABLE `anomaly_reports`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `location` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `report_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `description` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `severity` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_report_time`(`report_time` ASC) USING BTREE,
  INDEX `idx_severity`(`severity` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `asruex_logs`;

CREATE TABLE `asruex_logs`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `log_time` datetime NULL DEFAULT NULL,
  `ip` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `command` varchar(3) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `description` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `file_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_log_time`(`log_time` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_command`(`command` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 120693 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `botnet_communications_444`;

CREATE TABLE `botnet_communications_444`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `node_id` int NOT NULL COMMENT '关联的节点ID',
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点IP',
  `communication_time` timestamp NOT NULL COMMENT '通信时间（日志时间）',
  `received_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '接收时间',
  `longitude` float NULL DEFAULT NULL COMMENT '经度',
  `latitude` float NULL DEFAULT NULL COMMENT '纬度',
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '洲',
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ISP运营商',
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AS号',
  `event_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '事件类型',
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '通信状态',
  `is_china` tinyint(1) NULL DEFAULT 0 COMMENT '是否为中国节点',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_node_id`(`node_id` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_communication_time`(`communication_time` ASC) USING BTREE,
  INDEX `idx_received_at`(`received_at` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_is_china`(`is_china` ASC) USING BTREE,
  INDEX `idx_composite`(`ip` ASC, `communication_time` ASC) USING BTREE,
  CONSTRAINT `botnet_communications_444_ibfk_1` FOREIGN KEY (`node_id`) REFERENCES `botnet_nodes_444` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '僵尸网络节点通信记录表' ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `botnet_communications_88888`;

CREATE TABLE `botnet_communications_88888`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `node_id` int NOT NULL COMMENT '关联的节点ID',
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点IP',
  `communication_time` timestamp NOT NULL COMMENT '通信时间（日志时间）',
  `received_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '接收时间',
  `longitude` float NULL DEFAULT NULL COMMENT '经度',
  `latitude` float NULL DEFAULT NULL COMMENT '纬度',
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '洲',
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ISP运营商',
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AS号',
  `event_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '事件类型',
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '通信状态',
  `is_china` tinyint(1) NULL DEFAULT 0 COMMENT '是否为中国节点',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_node_id`(`node_id` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_communication_time`(`communication_time` ASC) USING BTREE,
  INDEX `idx_received_at`(`received_at` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_is_china`(`is_china` ASC) USING BTREE,
  INDEX `idx_composite`(`ip` ASC, `communication_time` ASC) USING BTREE,
  CONSTRAINT `botnet_communications_88888_ibfk_1` FOREIGN KEY (`node_id`) REFERENCES `botnet_nodes_88888` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '僵尸网络节点通信记录表' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `botnet_communications_andromeda`;

CREATE TABLE `botnet_communications_andromeda`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `node_id` int NOT NULL COMMENT '关联的节点ID',
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点IP',
  `communication_time` timestamp NOT NULL COMMENT '通信时间（日志时间）',
  `received_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '接收时间',
  `longitude` float NULL DEFAULT NULL COMMENT '经度',
  `latitude` float NULL DEFAULT NULL COMMENT '纬度',
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '洲',
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ISP运营商',
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AS号',
  `event_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '事件类型',
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '通信状态',
  `is_china` tinyint(1) NULL DEFAULT 0 COMMENT '是否为中国节点',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_unique_communication`(`ip` ASC, `communication_time` ASC) USING BTREE,
  INDEX `idx_communication_time`(`communication_time` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 241083 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '僵尸网络节点通信记录表' ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `botnet_communications_asruex`;

CREATE TABLE `botnet_communications_asruex`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `node_id` int NOT NULL COMMENT '关联的节点ID',
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点IP',
  `communication_time` timestamp NOT NULL COMMENT '通信时间（日志时间）',
  `received_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '接收时间',
  `longitude` float NULL DEFAULT NULL COMMENT '经度',
  `latitude` float NULL DEFAULT NULL COMMENT '纬度',
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '洲',
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ISP运营商',
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AS号',
  `event_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '事件类型',
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '通信状态',
  `is_china` tinyint(1) NULL DEFAULT 0 COMMENT '是否为中国节点',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_unique_communication`(`ip` ASC, `communication_time` ASC) USING BTREE,
  INDEX `idx_communication_time`(`communication_time` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 251925 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '僵尸网络节点通信记录表' ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `botnet_communications_autoupdate`;

CREATE TABLE `botnet_communications_autoupdate`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `node_id` int NOT NULL COMMENT '关联的节点ID',
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点IP',
  `communication_time` timestamp NOT NULL COMMENT '通信时间（日志时间）',
  `received_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '接收时间',
  `longitude` float NULL DEFAULT NULL COMMENT '经度',
  `latitude` float NULL DEFAULT NULL COMMENT '纬度',
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '洲',
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ISP运营商',
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AS号',
  `event_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '事件类型',
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '通信状态',
  `is_china` tinyint(1) NULL DEFAULT 0 COMMENT '是否为中国节点',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_node_id`(`node_id` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_communication_time`(`communication_time` ASC) USING BTREE,
  INDEX `idx_received_at`(`received_at` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_is_china`(`is_china` ASC) USING BTREE,
  INDEX `idx_composite`(`ip` ASC, `communication_time` ASC) USING BTREE,
  CONSTRAINT `botnet_communications_autoupdate_ibfk_1` FOREIGN KEY (`node_id`) REFERENCES `botnet_nodes_autoupdate` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '僵尸网络节点通信记录表' ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `botnet_communications_leethozer`;

CREATE TABLE `botnet_communications_leethozer`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `node_id` int NOT NULL COMMENT '关联的节点ID',
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点IP',
  `communication_time` timestamp NOT NULL COMMENT '通信时间（日志时间）',
  `received_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '接收时间',
  `longitude` float NULL DEFAULT NULL COMMENT '经度',
  `latitude` float NULL DEFAULT NULL COMMENT '纬度',
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '洲',
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ISP运营商',
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AS号',
  `event_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '事件类型',
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '通信状态',
  `is_china` tinyint(1) NULL DEFAULT 0 COMMENT '是否为中国节点',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_unique_communication`(`ip` ASC, `communication_time` ASC) USING BTREE,
  INDEX `idx_communication_time`(`communication_time` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 217628 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '僵尸网络节点通信记录表' ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `botnet_communications_moobot`;

CREATE TABLE `botnet_communications_moobot`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `node_id` int NOT NULL COMMENT '关联的节点ID',
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点IP',
  `communication_time` timestamp NOT NULL COMMENT '通信时间（日志时间）',
  `received_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '接收时间',
  `longitude` float NULL DEFAULT NULL COMMENT '经度',
  `latitude` float NULL DEFAULT NULL COMMENT '纬度',
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '洲',
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ISP运营商',
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AS号',
  `event_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '事件类型',
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '通信状态',
  `is_china` tinyint(1) NULL DEFAULT 0 COMMENT '是否为中国节点',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_unique_communication`(`ip` ASC, `communication_time` ASC) USING BTREE,
  INDEX `idx_communication_time`(`communication_time` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 919 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '僵尸网络节点通信记录表' ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `botnet_communications_mozi`;

CREATE TABLE `botnet_communications_mozi`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `node_id` int NOT NULL COMMENT '关联的节点ID',
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点IP',
  `communication_time` timestamp NOT NULL COMMENT '通信时间（日志时间）',
  `received_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '接收时间',
  `longitude` float NULL DEFAULT NULL COMMENT '经度',
  `latitude` float NULL DEFAULT NULL COMMENT '纬度',
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '洲',
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ISP运营商',
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AS号',
  `event_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '事件类型',
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '通信状态',
  `is_china` tinyint(1) NULL DEFAULT 0 COMMENT '是否为中国节点',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_unique_communication`(`ip` ASC, `communication_time` ASC) USING BTREE,
  INDEX `idx_communication_time`(`communication_time` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 295109 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '僵尸网络节点通信记录表' ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `botnet_communications_ramnit`;

CREATE TABLE `botnet_communications_ramnit`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `node_id` int NOT NULL COMMENT '关联的节点ID',
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点IP',
  `communication_time` timestamp NOT NULL COMMENT '通信时间（日志时间）',
  `received_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '接收时间',
  `longitude` float NULL DEFAULT NULL COMMENT '经度',
  `latitude` float NULL DEFAULT NULL COMMENT '纬度',
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '洲',
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ISP运营商',
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AS号',
  `event_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '事件类型',
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '通信状态',
  `is_china` tinyint(1) NULL DEFAULT 0 COMMENT '是否为中国节点',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_unique_communication`(`ip` ASC, `communication_time` ASC) USING BTREE,
  INDEX `idx_communication_time`(`communication_time` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_ip_comm_time_ramnit`(`ip` ASC, `communication_time` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 133071 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '僵尸网络节点通信记录表' ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `botnet_communications_test`;

CREATE TABLE `botnet_communications_test`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `node_id` int NOT NULL COMMENT '关联的节点ID',
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点IP',
  `communication_time` timestamp NOT NULL COMMENT '通信时间（日志时间）',
  `received_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '接收时间',
  `longitude` float NULL DEFAULT NULL COMMENT '经度',
  `latitude` float NULL DEFAULT NULL COMMENT '纬度',
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '洲',
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ISP运营商',
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AS号',
  `event_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '事件类型',
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '通信状态',
  `is_china` tinyint(1) NULL DEFAULT 0 COMMENT '是否为中国节点',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_node_id`(`node_id` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_communication_time`(`communication_time` ASC) USING BTREE,
  INDEX `idx_received_at`(`received_at` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_is_china`(`is_china` ASC) USING BTREE,
  INDEX `idx_composite`(`ip` ASC, `communication_time` ASC) USING BTREE,
  CONSTRAINT `botnet_communications_test_ibfk_1` FOREIGN KEY (`node_id`) REFERENCES `botnet_nodes_test` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 294501 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '僵尸网络节点通信记录表' ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `botnet_communications_test222`;

CREATE TABLE `botnet_communications_test222`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `node_id` int NOT NULL COMMENT '关联的节点ID',
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点IP',
  `communication_time` timestamp NOT NULL COMMENT '通信时间（日志时间）',
  `received_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '接收时间',
  `longitude` float NULL DEFAULT NULL COMMENT '经度',
  `latitude` float NULL DEFAULT NULL COMMENT '纬度',
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '洲',
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ISP运营商',
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AS号',
  `event_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '事件类型',
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '通信状态',
  `is_china` tinyint(1) NULL DEFAULT 0 COMMENT '是否为中国节点',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_node_id`(`node_id` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_communication_time`(`communication_time` ASC) USING BTREE,
  INDEX `idx_received_at`(`received_at` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_is_china`(`is_china` ASC) USING BTREE,
  INDEX `idx_composite`(`ip` ASC, `communication_time` ASC) USING BTREE,
  CONSTRAINT `botnet_communications_test222_ibfk_1` FOREIGN KEY (`node_id`) REFERENCES `botnet_nodes_test222` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '僵尸网络节点通信记录表' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `botnet_communications_test333`;

CREATE TABLE `botnet_communications_test333`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `node_id` int NOT NULL COMMENT '关联的节点ID',
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点IP',
  `communication_time` timestamp NOT NULL COMMENT '通信时间（日志时间）',
  `received_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '接收时间',
  `longitude` float NULL DEFAULT NULL COMMENT '经度',
  `latitude` float NULL DEFAULT NULL COMMENT '纬度',
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '洲',
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ISP运营商',
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AS号',
  `event_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '事件类型',
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '通信状态',
  `is_china` tinyint(1) NULL DEFAULT 0 COMMENT '是否为中国节点',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_node_id`(`node_id` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_communication_time`(`communication_time` ASC) USING BTREE,
  INDEX `idx_received_at`(`received_at` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_is_china`(`is_china` ASC) USING BTREE,
  INDEX `idx_composite`(`ip` ASC, `communication_time` ASC) USING BTREE,
  CONSTRAINT `botnet_communications_test333_ibfk_1` FOREIGN KEY (`node_id`) REFERENCES `botnet_nodes_test333` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '僵尸网络节点通信记录表' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `botnet_communications_test444`;

CREATE TABLE `botnet_communications_test444`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `node_id` int NOT NULL COMMENT '关联的节点ID',
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点IP',
  `communication_time` timestamp NOT NULL COMMENT '通信时间（日志时间）',
  `received_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '接收时间',
  `longitude` float NULL DEFAULT NULL COMMENT '经度',
  `latitude` float NULL DEFAULT NULL COMMENT '纬度',
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '洲',
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ISP运营商',
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AS号',
  `event_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '事件类型',
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '通信状态',
  `is_china` tinyint(1) NULL DEFAULT 0 COMMENT '是否为中国节点',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_node_id`(`node_id` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_communication_time`(`communication_time` ASC) USING BTREE,
  INDEX `idx_received_at`(`received_at` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_is_china`(`is_china` ASC) USING BTREE,
  INDEX `idx_composite`(`ip` ASC, `communication_time` ASC) USING BTREE,
  CONSTRAINT `botnet_communications_test444_ibfk_1` FOREIGN KEY (`node_id`) REFERENCES `botnet_nodes_test444` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '僵尸网络节点通信记录表' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `botnet_nodes_444`;

CREATE TABLE `botnet_nodes_444`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点IP地址',
  `longitude` float NULL DEFAULT NULL COMMENT '经度',
  `latitude` float NULL DEFAULT NULL COMMENT '纬度',
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '洲',
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ISP运营商',
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AS号',
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '节点状态',
  `first_seen` timestamp NULL DEFAULT NULL COMMENT '首次发现时间（日志时间）',
  `last_seen` timestamp NULL DEFAULT NULL COMMENT '最后通信时间（日志时间）',
  `communication_count` int NULL DEFAULT 0 COMMENT '通信次数',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  `is_china` tinyint(1) NULL DEFAULT 0 COMMENT '是否为中国节点',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_unique_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_first_seen`(`first_seen` ASC) USING BTREE,
  INDEX `idx_last_seen`(`last_seen` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_is_china`(`is_china` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '僵尸网络节点基本信息表（汇总）' ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `botnet_nodes_88888`;

CREATE TABLE `botnet_nodes_88888`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点IP地址',
  `longitude` float NULL DEFAULT NULL COMMENT '经度',
  `latitude` float NULL DEFAULT NULL COMMENT '纬度',
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '洲',
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ISP运营商',
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AS号',
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '节点状态',
  `first_seen` timestamp NULL DEFAULT NULL COMMENT '首次发现时间（日志时间）',
  `last_seen` timestamp NULL DEFAULT NULL COMMENT '最后通信时间（日志时间）',
  `communication_count` int NULL DEFAULT 0 COMMENT '通信次数',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  `is_china` tinyint(1) NULL DEFAULT 0 COMMENT '是否为中国节点',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_unique_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_first_seen`(`first_seen` ASC) USING BTREE,
  INDEX `idx_last_seen`(`last_seen` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_is_china`(`is_china` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '僵尸网络节点基本信息表（汇总）' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `botnet_nodes_andromeda`;

CREATE TABLE `botnet_nodes_andromeda`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `longitude` float NULL DEFAULT NULL,
  `latitude` float NULL DEFAULT NULL,
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active',
  `first_seen` timestamp NULL DEFAULT NULL COMMENT '首次发现时间（日志时间）',
  `created_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '节点首次写入数据库的时间',
  `last_seen` timestamp NULL DEFAULT NULL COMMENT '最后通信时间（日志时间）',
  `is_china` tinyint(1) NULL DEFAULT 0,
  `communication_count` int NULL DEFAULT 0 COMMENT '通信次数',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_unique_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_is_china`(`is_china` ASC) USING BTREE,
  INDEX `idx_active_time`(`first_seen` ASC) USING BTREE,
  INDEX `idx_created_time`(`created_time` ASC) USING BTREE,
  INDEX `idx_updated_at`(`last_seen` ASC) USING BTREE,
  INDEX `idx_first_seen`(`first_seen` ASC) USING BTREE,
  INDEX `idx_last_seen`(`last_seen` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_country`(`country` ASC) USING BTREE,
  INDEX `idx_province`(`province` ASC) USING BTREE,
  INDEX `idx_city`(`city` ASC) USING BTREE,
  INDEX `idx_country_province_city`(`country` ASC, `province` ASC, `city` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 241116 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `botnet_nodes_asruex`;

CREATE TABLE `botnet_nodes_asruex`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `longitude` float NULL DEFAULT NULL,
  `latitude` float NULL DEFAULT NULL,
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active',
  `first_seen` timestamp NULL DEFAULT NULL COMMENT '首次发现时间（日志时间）',
  `created_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '节点首次写入数据库的时间',
  `last_seen` timestamp NULL DEFAULT NULL COMMENT '最后通信时间（日志时间）',
  `is_china` tinyint(1) NULL DEFAULT 0,
  `communication_count` int NULL DEFAULT 0 COMMENT '通信次数',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_unique_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_is_china`(`is_china` ASC) USING BTREE,
  INDEX `idx_active_time`(`first_seen` ASC) USING BTREE,
  INDEX `idx_created_time`(`created_time` ASC) USING BTREE,
  INDEX `idx_updated_at`(`last_seen` ASC) USING BTREE,
  INDEX `idx_first_seen`(`first_seen` ASC) USING BTREE,
  INDEX `idx_last_seen`(`last_seen` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_country`(`country` ASC) USING BTREE,
  INDEX `idx_province`(`province` ASC) USING BTREE,
  INDEX `idx_city`(`city` ASC) USING BTREE,
  INDEX `idx_country_province_city`(`country` ASC, `province` ASC, `city` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 252003 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `botnet_nodes_autoupdate`;

CREATE TABLE `botnet_nodes_autoupdate`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点IP地址',
  `longitude` float NULL DEFAULT NULL COMMENT '经度',
  `latitude` float NULL DEFAULT NULL COMMENT '纬度',
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '洲',
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ISP运营商',
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AS号',
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '节点状态',
  `first_seen` timestamp NULL DEFAULT NULL COMMENT '首次发现时间（日志时间）',
  `last_seen` timestamp NULL DEFAULT NULL COMMENT '最后通信时间（日志时间）',
  `communication_count` int NULL DEFAULT 0 COMMENT '通信次数',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  `is_china` tinyint(1) NULL DEFAULT 0 COMMENT '是否为中国节点',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_unique_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_first_seen`(`first_seen` ASC) USING BTREE,
  INDEX `idx_last_seen`(`last_seen` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_is_china`(`is_china` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '僵尸网络节点基本信息表（汇总）' ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `botnet_nodes_leethozer`;

CREATE TABLE `botnet_nodes_leethozer`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `longitude` float NULL DEFAULT NULL,
  `latitude` float NULL DEFAULT NULL,
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active',
  `first_seen` timestamp NULL DEFAULT NULL COMMENT '首次发现时间（日志时间）',
  `created_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '节点首次写入数据库的时间',
  `last_seen` timestamp NULL DEFAULT NULL COMMENT '最后通信时间（日志时间）',
  `is_china` tinyint(1) NULL DEFAULT 0,
  `communication_count` int NULL DEFAULT 0 COMMENT '通信次数',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_unique_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_is_china`(`is_china` ASC) USING BTREE,
  INDEX `idx_active_time`(`first_seen` ASC) USING BTREE,
  INDEX `idx_created_time`(`created_time` ASC) USING BTREE,
  INDEX `idx_updated_at`(`last_seen` ASC) USING BTREE,
  INDEX `idx_first_seen`(`first_seen` ASC) USING BTREE,
  INDEX `idx_last_seen`(`last_seen` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_country`(`country` ASC) USING BTREE,
  INDEX `idx_province`(`province` ASC) USING BTREE,
  INDEX `idx_city`(`city` ASC) USING BTREE,
  INDEX `idx_country_province_city`(`country` ASC, `province` ASC, `city` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 217657 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `botnet_nodes_moobot`;

CREATE TABLE `botnet_nodes_moobot`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `longitude` float NULL DEFAULT NULL,
  `latitude` float NULL DEFAULT NULL,
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active',
  `first_seen` timestamp NULL DEFAULT NULL COMMENT '首次发现时间（日志时间）',
  `created_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '节点首次写入数据库的时间',
  `last_seen` timestamp NULL DEFAULT NULL COMMENT '最后通信时间（日志时间）',
  `is_china` tinyint(1) NULL DEFAULT 0,
  `communication_count` int NULL DEFAULT 0 COMMENT '通信次数',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_unique_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_is_china`(`is_china` ASC) USING BTREE,
  INDEX `idx_active_time`(`first_seen` ASC) USING BTREE,
  INDEX `idx_created_time`(`created_time` ASC) USING BTREE,
  INDEX `idx_updated_at`(`last_seen` ASC) USING BTREE,
  INDEX `idx_first_seen`(`first_seen` ASC) USING BTREE,
  INDEX `idx_last_seen`(`last_seen` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_country`(`country` ASC) USING BTREE,
  INDEX `idx_province`(`province` ASC) USING BTREE,
  INDEX `idx_city`(`city` ASC) USING BTREE,
  INDEX `idx_country_province_city`(`country` ASC, `province` ASC, `city` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 921 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `botnet_nodes_mozi`;

CREATE TABLE `botnet_nodes_mozi`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `longitude` float NULL DEFAULT NULL,
  `latitude` float NULL DEFAULT NULL,
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active',
  `first_seen` timestamp NULL DEFAULT NULL COMMENT '首次发现时间（日志时间）',
  `created_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '节点首次写入数据库的时间',
  `last_seen` timestamp NULL DEFAULT NULL COMMENT '最后通信时间（日志时间）',
  `is_china` tinyint(1) NULL DEFAULT 0,
  `communication_count` int NULL DEFAULT 0 COMMENT '通信次数',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_unique_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_is_china`(`is_china` ASC) USING BTREE,
  INDEX `idx_active_time`(`first_seen` ASC) USING BTREE,
  INDEX `idx_created_time`(`created_time` ASC) USING BTREE,
  INDEX `idx_updated_at`(`last_seen` ASC) USING BTREE,
  INDEX `idx_first_seen`(`first_seen` ASC) USING BTREE,
  INDEX `idx_last_seen`(`last_seen` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_country`(`country` ASC) USING BTREE,
  INDEX `idx_province`(`province` ASC) USING BTREE,
  INDEX `idx_city`(`city` ASC) USING BTREE,
  INDEX `idx_country_province_city`(`country` ASC, `province` ASC, `city` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 295208 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `botnet_nodes_ramnit`;

CREATE TABLE `botnet_nodes_ramnit`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `longitude` float NULL DEFAULT NULL,
  `latitude` float NULL DEFAULT NULL,
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active',
  `active_time` timestamp NULL DEFAULT NULL COMMENT '节点激活时间（日志中的时间）',
  `first_seen` timestamp NULL DEFAULT NULL COMMENT '首次发现时间（日志时间）',
  `created_time` timestamp NULL DEFAULT NULL COMMENT '节点首次写入数据库的时间',
  `last_seen` timestamp NULL DEFAULT NULL COMMENT '最后通信时间（日志时间）',
  `is_china` tinyint(1) NULL DEFAULT 0,
  `communication_count` int NULL DEFAULT 0 COMMENT '通信次数',
  `updated_at` timestamp NULL DEFAULT NULL COMMENT '节点最新一次响应时间（日志中的时间）',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_unique_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_is_china`(`is_china` ASC) USING BTREE,
  INDEX `idx_log_time`(`first_seen` ASC) USING BTREE,
  INDEX `idx_first_seen`(`first_seen` ASC) USING BTREE,
  INDEX `idx_last_seen`(`last_seen` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_ip_created_ramnit`(`ip` ASC, `created_time` ASC) USING BTREE,
  INDEX `idx_location_china_ramnit`(`country` ASC, `province` ASC, `city` ASC, `is_china` ASC) USING BTREE,
  INDEX `idx_country`(`country` ASC) USING BTREE,
  INDEX `idx_province`(`province` ASC) USING BTREE,
  INDEX `idx_city`(`city` ASC) USING BTREE,
  INDEX `idx_country_province_city`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_updated_at`(`updated_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 124607 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `botnet_nodes_test`;

CREATE TABLE `botnet_nodes_test`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点IP地址',
  `longitude` float NULL DEFAULT NULL COMMENT '经度',
  `latitude` float NULL DEFAULT NULL COMMENT '纬度',
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '洲',
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ISP运营商',
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AS号',
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '节点状态',
  `active_time` timestamp NULL DEFAULT NULL COMMENT '节点激活时间（日志中的时间）',
  `first_seen` timestamp NULL DEFAULT NULL COMMENT '首次发现时间（日志时间）',
  `last_seen` timestamp NULL DEFAULT NULL COMMENT '最后通信时间（日志时间）',
  `communication_count` int NULL DEFAULT 0 COMMENT '通信次数',
  `created_time` timestamp NULL DEFAULT NULL COMMENT '节点首次写入数据库的时间',
  `updated_at` timestamp NULL DEFAULT NULL COMMENT '节点最新一次响应时间（日志中的时间）',
  `is_china` tinyint(1) NULL DEFAULT 0 COMMENT '是否为中国节点',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_unique_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_first_seen`(`first_seen` ASC) USING BTREE,
  INDEX `idx_last_seen`(`last_seen` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_is_china`(`is_china` ASC) USING BTREE,
  INDEX `idx_location_china_test`(`country` ASC, `province` ASC, `city` ASC, `is_china` ASC) USING BTREE,
  INDEX `idx_active_time`(`active_time` ASC) USING BTREE,
  INDEX `idx_country`(`country` ASC) USING BTREE,
  INDEX `idx_province`(`province` ASC) USING BTREE,
  INDEX `idx_city`(`city` ASC) USING BTREE,
  INDEX `idx_country_province_city`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_updated_at`(`updated_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 328548 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '僵尸网络节点基本信息表（汇总）' ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `botnet_nodes_test222`;

CREATE TABLE `botnet_nodes_test222`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点IP地址',
  `longitude` float NULL DEFAULT NULL COMMENT '经度',
  `latitude` float NULL DEFAULT NULL COMMENT '纬度',
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '洲',
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ISP运营商',
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AS号',
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '节点状态',
  `first_seen` timestamp NULL DEFAULT NULL COMMENT '首次发现时间（日志时间）',
  `last_seen` timestamp NULL DEFAULT NULL COMMENT '最后通信时间（日志时间）',
  `communication_count` int NULL DEFAULT 0 COMMENT '通信次数',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  `is_china` tinyint(1) NULL DEFAULT 0 COMMENT '是否为中国节点',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_unique_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_first_seen`(`first_seen` ASC) USING BTREE,
  INDEX `idx_last_seen`(`last_seen` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_is_china`(`is_china` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '僵尸网络节点基本信息表（汇总）' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `botnet_nodes_test333`;

CREATE TABLE `botnet_nodes_test333`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点IP地址',
  `longitude` float NULL DEFAULT NULL COMMENT '经度',
  `latitude` float NULL DEFAULT NULL COMMENT '纬度',
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '洲',
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ISP运营商',
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AS号',
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '节点状态',
  `first_seen` timestamp NULL DEFAULT NULL COMMENT '首次发现时间（日志时间）',
  `last_seen` timestamp NULL DEFAULT NULL COMMENT '最后通信时间（日志时间）',
  `communication_count` int NULL DEFAULT 0 COMMENT '通信次数',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  `is_china` tinyint(1) NULL DEFAULT 0 COMMENT '是否为中国节点',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_unique_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_first_seen`(`first_seen` ASC) USING BTREE,
  INDEX `idx_last_seen`(`last_seen` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_is_china`(`is_china` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '僵尸网络节点基本信息表（汇总）' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `botnet_nodes_test444`;

CREATE TABLE `botnet_nodes_test444`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点IP地址',
  `longitude` float NULL DEFAULT NULL COMMENT '经度',
  `latitude` float NULL DEFAULT NULL COMMENT '纬度',
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `continent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '洲',
  `isp` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ISP运营商',
  `asn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AS号',
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '节点状态',
  `first_seen` timestamp NULL DEFAULT NULL COMMENT '首次发现时间（日志时间）',
  `last_seen` timestamp NULL DEFAULT NULL COMMENT '最后通信时间（日志时间）',
  `communication_count` int NULL DEFAULT 0 COMMENT '通信次数',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  `is_china` tinyint(1) NULL DEFAULT 0 COMMENT '是否为中国节点',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_unique_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_ip`(`ip` ASC) USING BTREE,
  INDEX `idx_location`(`country` ASC, `province` ASC, `city` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_first_seen`(`first_seen` ASC) USING BTREE,
  INDEX `idx_last_seen`(`last_seen` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_is_china`(`is_china` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '僵尸网络节点基本信息表（汇总）' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `botnet_timeset_88888`;

CREATE TABLE `botnet_timeset_88888`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL COMMENT '日期',
  `count` int NOT NULL DEFAULT 0 COMMENT '节点数量',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `date`(`date` ASC) USING BTREE,
  INDEX `idx_date`(`date` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '88888僵尸网络每日节点数量统计表' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `botnet_timeset_andromeda`;

CREATE TABLE `botnet_timeset_andromeda`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL COMMENT '日期',
  `global_count` int NOT NULL DEFAULT 0 COMMENT '全球节点数量',
  `china_count` int NOT NULL DEFAULT 0 COMMENT '中国节点数量',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `date`(`date` ASC) USING BTREE,
  INDEX `idx_date`(`date` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 47 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'andromeda僵尸网络每日节点数量统计表' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `botnet_timeset_asruex`;

CREATE TABLE `botnet_timeset_asruex`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL COMMENT '日期',
  `global_count` int NOT NULL DEFAULT 0 COMMENT '全球节点数量',
  `china_count` int NOT NULL DEFAULT 0 COMMENT '中国节点数量',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `date`(`date` ASC) USING BTREE,
  INDEX `idx_date`(`date` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 47 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'asruex僵尸网络每日节点数量统计表' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `botnet_timeset_leethozer`;

CREATE TABLE `botnet_timeset_leethozer`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL COMMENT '日期',
  `global_count` int NOT NULL DEFAULT 0 COMMENT '全球节点数量',
  `china_count` int NOT NULL DEFAULT 0 COMMENT '中国节点数量',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `date`(`date` ASC) USING BTREE,
  INDEX `idx_date`(`date` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 47 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'leethozer僵尸网络每日节点数量统计表' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `botnet_timeset_moobot`;

CREATE TABLE `botnet_timeset_moobot`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL COMMENT '日期',
  `global_count` int NOT NULL DEFAULT 0 COMMENT '全球节点数量',
  `china_count` int NOT NULL DEFAULT 0 COMMENT '中国节点数量',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `date`(`date` ASC) USING BTREE,
  INDEX `idx_date`(`date` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 47 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'moobot僵尸网络每日节点数量统计表' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `botnet_timeset_mozi`;

CREATE TABLE `botnet_timeset_mozi`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL COMMENT '日期',
  `global_count` int NOT NULL DEFAULT 0 COMMENT '全球节点数量',
  `china_count` int NOT NULL DEFAULT 0 COMMENT '中国节点数量',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `date`(`date` ASC) USING BTREE,
  INDEX `idx_date`(`date` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 47 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'mozi僵尸网络每日节点数量统计表' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `botnet_timeset_ramnit`;

CREATE TABLE `botnet_timeset_ramnit`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL COMMENT '日期',
  `global_count` int NOT NULL DEFAULT 0 COMMENT '全球节点数量',
  `china_count` int NOT NULL DEFAULT 0 COMMENT '中国节点数量',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `date`(`date` ASC) USING BTREE,
  INDEX `idx_date`(`date` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 47 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'ramnit僵尸网络每日节点数量统计表' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `botnet_timeset_test`;

CREATE TABLE `botnet_timeset_test`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL COMMENT '日期',
  `global_count` int NOT NULL DEFAULT 0 COMMENT '全球节点数量',
  `china_count` int NOT NULL DEFAULT 0 COMMENT '中国节点数量',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `date`(`date` ASC) USING BTREE,
  INDEX `idx_date`(`date` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 47 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'test僵尸网络每日节点数量统计表' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `botnet_timeset_test222`;

CREATE TABLE `botnet_timeset_test222`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL COMMENT '日期',
  `count` int NOT NULL DEFAULT 0 COMMENT '节点数量',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `date`(`date` ASC) USING BTREE,
  INDEX `idx_date`(`date` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'test222僵尸网络每日节点数量统计表' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `botnet_timeset_test333`;

CREATE TABLE `botnet_timeset_test333`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL COMMENT '日期',
  `count` int NOT NULL DEFAULT 0 COMMENT '节点数量',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `date`(`date` ASC) USING BTREE,
  INDEX `idx_date`(`date` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'test333僵尸网络每日节点数量统计表' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `botnet_timeset_test444`;

CREATE TABLE `botnet_timeset_test444`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL COMMENT '日期',
  `count` int NOT NULL DEFAULT 0 COMMENT '节点数量',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `date`(`date` ASC) USING BTREE,
  INDEX `idx_date`(`date` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'test444僵尸网络每日节点数量统计表' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `botnet_types`;

CREATE TABLE `botnet_types`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `display_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL,
  `table_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `clean_methods` json NULL COMMENT '支持的清理方法',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `name`(`name` ASC) USING BTREE,
  INDEX `idx_name`(`name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 19 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `china_botnet_444`;

CREATE TABLE `china_botnet_444`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `municipality` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `infected_num` int NULL DEFAULT 0 COMMENT '感染数量（节点数）',
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  `created_at` timestamp NULL DEFAULT NULL COMMENT '该地区第一个节点的创建时间',
  `updated_at` timestamp NULL DEFAULT NULL COMMENT '该地区最新节点的更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_location`(`province` ASC, `municipality` ASC) USING BTREE,
  INDEX `idx_province`(`province` ASC) USING BTREE,
  INDEX `idx_infected_num`(`infected_num` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  INDEX `idx_updated_at`(`updated_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '中国地区僵尸网络统计表(按省市)' ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `china_botnet_88888`;

CREATE TABLE `china_botnet_88888`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `municipality` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `infected_num` int NULL DEFAULT 0 COMMENT '感染数量（节点数）',
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  `created_at` timestamp NULL DEFAULT NULL COMMENT '该地区第一个节点的创建时间',
  `updated_at` timestamp NULL DEFAULT NULL COMMENT '该地区最新节点的更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_location`(`province` ASC, `municipality` ASC) USING BTREE,
  INDEX `idx_province`(`province` ASC) USING BTREE,
  INDEX `idx_infected_num`(`infected_num` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  INDEX `idx_updated_at`(`updated_at` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '中国地区僵尸网络统计表(按省市)' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `china_botnet_andromeda`;

CREATE TABLE `china_botnet_andromeda`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `municipality` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `infected_num` int NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_location`(`province`, `municipality`) USING BTREE,
  INDEX `idx_province`(`province`) USING BTREE,
  INDEX `idx_municipality`(`municipality`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 415 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `china_botnet_asruex`;

CREATE TABLE `china_botnet_asruex`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `municipality` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `infected_num` int NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_location`(`province`, `municipality`) USING BTREE,
  INDEX `idx_province`(`province`) USING BTREE,
  INDEX `idx_municipality`(`municipality`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 414 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `china_botnet_autoupdate`;

CREATE TABLE `china_botnet_autoupdate`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `municipality` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `infected_num` int NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_province`(`province`) USING BTREE,
  INDEX `idx_municipality`(`municipality`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 1453 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `china_botnet_leethozer`;

CREATE TABLE `china_botnet_leethozer`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `municipality` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `infected_num` int NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_location`(`province`, `municipality`) USING BTREE,
  INDEX `idx_province`(`province`) USING BTREE,
  INDEX `idx_municipality`(`municipality`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 417 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `china_botnet_mirai`;

CREATE TABLE `china_botnet_mirai`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `municipality` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `infected_num` int NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_province`(`province`) USING BTREE,
  INDEX `idx_municipality`(`municipality`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 1453 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `china_botnet_moobot`;

CREATE TABLE `china_botnet_moobot`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `municipality` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `infected_num` int NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_location`(`province`, `municipality`) USING BTREE,
  INDEX `idx_province`(`province`) USING BTREE,
  INDEX `idx_municipality`(`municipality`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 17 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `china_botnet_mozi`;

CREATE TABLE `china_botnet_mozi`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `municipality` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `infected_num` int NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_location`(`province`, `municipality`) USING BTREE,
  INDEX `idx_province`(`province`) USING BTREE,
  INDEX `idx_municipality`(`municipality`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 415 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `china_botnet_ramnit`;

CREATE TABLE `china_botnet_ramnit`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `municipality` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `infected_num` int NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_location`(`province`, `municipality`) USING BTREE,
  INDEX `idx_province`(`province`) USING BTREE,
  INDEX `idx_municipality`(`municipality`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 447 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `china_botnet_template`;

CREATE TABLE `china_botnet_template`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `municipality` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `infected_num` int NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_province`(`province`) USING BTREE,
  INDEX `idx_municipality`(`municipality`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 1453 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `china_botnet_test`;

CREATE TABLE `china_botnet_test`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `municipality` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `infected_num` int NULL DEFAULT 0 COMMENT '感染数量（节点数）',
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  `created_at` timestamp NULL DEFAULT NULL COMMENT '该地区第一个节点的创建时间',
  `updated_at` timestamp NULL DEFAULT NULL COMMENT '该地区最新节点的更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_location`(`province` ASC, `municipality` ASC) USING BTREE,
  INDEX `idx_province`(`province` ASC) USING BTREE,
  INDEX `idx_infected_num`(`infected_num` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  INDEX `idx_updated_at`(`updated_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 622 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '中国地区僵尸网络统计表(按省市)' ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `china_botnet_test222`;

CREATE TABLE `china_botnet_test222`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `municipality` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `infected_num` int NULL DEFAULT 0 COMMENT '感染数量（节点数）',
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  `created_at` timestamp NULL DEFAULT NULL COMMENT '该地区第一个节点的创建时间',
  `updated_at` timestamp NULL DEFAULT NULL COMMENT '该地区最新节点的更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_location`(`province` ASC, `municipality` ASC) USING BTREE,
  INDEX `idx_province`(`province` ASC) USING BTREE,
  INDEX `idx_infected_num`(`infected_num` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  INDEX `idx_updated_at`(`updated_at` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '中国地区僵尸网络统计表(按省市)' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `china_botnet_test333`;

CREATE TABLE `china_botnet_test333`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `municipality` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `infected_num` int NULL DEFAULT 0 COMMENT '感染数量（节点数）',
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  `created_at` timestamp NULL DEFAULT NULL COMMENT '该地区第一个节点的创建时间',
  `updated_at` timestamp NULL DEFAULT NULL COMMENT '该地区最新节点的更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_location`(`province` ASC, `municipality` ASC) USING BTREE,
  INDEX `idx_province`(`province` ASC) USING BTREE,
  INDEX `idx_infected_num`(`infected_num` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  INDEX `idx_updated_at`(`updated_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '中国地区僵尸网络统计表(按省市)' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `china_botnet_test444`;

CREATE TABLE `china_botnet_test444`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `municipality` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `infected_num` int NULL DEFAULT 0 COMMENT '感染数量（节点数）',
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  `created_at` timestamp NULL DEFAULT NULL COMMENT '该地区第一个节点的创建时间',
  `updated_at` timestamp NULL DEFAULT NULL COMMENT '该地区最新节点的更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_location`(`province` ASC, `municipality` ASC) USING BTREE,
  INDEX `idx_province`(`province` ASC) USING BTREE,
  INDEX `idx_infected_num`(`infected_num` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  INDEX `idx_updated_at`(`updated_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '中国地区僵尸网络统计表(按省市)' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `domain_blacklist`;

CREATE TABLE `domain_blacklist`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `domain` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `description` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `domain`(`domain` ASC) USING BTREE,
  INDEX `idx_domain`(`domain` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `global_botnet_444`;

CREATE TABLE `global_botnet_444`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `country` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `infected_num` int NULL DEFAULT 0 COMMENT '感染数量（节点数）',
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  `created_at` timestamp NULL DEFAULT NULL COMMENT '该国家第一个节点的创建时间',
  `updated_at` timestamp NULL DEFAULT NULL COMMENT '该国家最新节点的更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_country`(`country` ASC) USING BTREE,
  INDEX `idx_infected_num`(`infected_num` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  INDEX `idx_updated_at`(`updated_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '全球僵尸网络统计表(按国家)' ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `global_botnet_88888`;

CREATE TABLE `global_botnet_88888`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `country` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `infected_num` int NULL DEFAULT 0 COMMENT '感染数量（节点数）',
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  `created_at` timestamp NULL DEFAULT NULL COMMENT '该国家第一个节点的创建时间',
  `updated_at` timestamp NULL DEFAULT NULL COMMENT '该国家最新节点的更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_country`(`country` ASC) USING BTREE,
  INDEX `idx_infected_num`(`infected_num` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  INDEX `idx_updated_at`(`updated_at` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '全球僵尸网络统计表(按国家)' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `global_botnet_andromeda`;

CREATE TABLE `global_botnet_andromeda`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `country` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `infected_num` int NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_country`(`country`) USING BTREE,
  INDEX `idx_infected_num`(`infected_num`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 203 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `global_botnet_asruex`;

CREATE TABLE `global_botnet_asruex`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `country` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `infected_num` int NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_country`(`country`) USING BTREE,
  INDEX `idx_infected_num`(`infected_num`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 200 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `global_botnet_autoupdate`;

CREATE TABLE `global_botnet_autoupdate`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `country` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `infected_num` int NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_country`(`country`) USING BTREE,
  INDEX `idx_infected_num`(`infected_num`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 191 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `global_botnet_leethozer`;

CREATE TABLE `global_botnet_leethozer`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `country` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `infected_num` int NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_country`(`country`) USING BTREE,
  INDEX `idx_infected_num`(`infected_num`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 198 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `global_botnet_moobot`;

CREATE TABLE `global_botnet_moobot`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `country` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `infected_num` int NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_country`(`country`) USING BTREE,
  INDEX `idx_infected_num`(`infected_num`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 75 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `global_botnet_mozi`;

CREATE TABLE `global_botnet_mozi`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `country` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `infected_num` int NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_country`(`country`) USING BTREE,
  INDEX `idx_infected_num`(`infected_num`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 211 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `global_botnet_ramnit`;

CREATE TABLE `global_botnet_ramnit`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `country` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `infected_num` int NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_country`(`country`) USING BTREE,
  INDEX `idx_infected_num`(`infected_num`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 169 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `global_botnet_template`;

CREATE TABLE `global_botnet_template`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `country` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `infected_num` int NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_country`(`country`) USING BTREE,
  INDEX `idx_infected_num`(`infected_num`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 194 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `global_botnet_test`;

CREATE TABLE `global_botnet_test`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `country` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `infected_num` int NULL DEFAULT 0 COMMENT '感染数量（节点数）',
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  `created_at` timestamp NULL DEFAULT NULL COMMENT '该国家第一个节点的创建时间',
  `updated_at` timestamp NULL DEFAULT NULL COMMENT '该国家最新节点的更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_country`(`country` ASC) USING BTREE,
  INDEX `idx_infected_num`(`infected_num` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  INDEX `idx_updated_at`(`updated_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 288 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '全球僵尸网络统计表(按国家)' ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `global_botnet_test222`;

CREATE TABLE `global_botnet_test222`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `country` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `infected_num` int NULL DEFAULT 0 COMMENT '感染数量（节点数）',
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  `created_at` timestamp NULL DEFAULT NULL COMMENT '该国家第一个节点的创建时间',
  `updated_at` timestamp NULL DEFAULT NULL COMMENT '该国家最新节点的更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_country`(`country` ASC) USING BTREE,
  INDEX `idx_infected_num`(`infected_num` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  INDEX `idx_updated_at`(`updated_at` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '全球僵尸网络统计表(按国家)' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `global_botnet_test333`;

CREATE TABLE `global_botnet_test333`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `country` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `infected_num` int NULL DEFAULT 0 COMMENT '感染数量（节点数）',
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  `created_at` timestamp NULL DEFAULT NULL COMMENT '该国家第一个节点的创建时间',
  `updated_at` timestamp NULL DEFAULT NULL COMMENT '该国家最新节点的更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_country`(`country` ASC) USING BTREE,
  INDEX `idx_infected_num`(`infected_num` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  INDEX `idx_updated_at`(`updated_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '全球僵尸网络统计表(按国家)' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `global_botnet_test444`;

CREATE TABLE `global_botnet_test444`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `country` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `infected_num` int NULL DEFAULT 0 COMMENT '感染数量（节点数）',
  `communication_count` int NULL DEFAULT 0 COMMENT '通信总次数',
  `created_at` timestamp NULL DEFAULT NULL COMMENT '该国家第一个节点的创建时间',
  `updated_at` timestamp NULL DEFAULT NULL COMMENT '该国家最新节点的更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_country`(`country` ASC) USING BTREE,
  INDEX `idx_infected_num`(`infected_num` ASC) USING BTREE,
  INDEX `idx_communication_count`(`communication_count` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  INDEX `idx_updated_at`(`updated_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '全球僵尸网络统计表(按国家)' ROW_FORMAT = Dynamic;

DROP TABLE IF EXISTS `global_botnets`;

CREATE TABLE `global_botnets`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `country` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `botnet_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `infected_num` int NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_country_botnet`(`country` ASC, `botnet_type` ASC) USING BTREE,
  INDEX `idx_botnet_type`(`botnet_type` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 571 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `ip_blacklist`;

CREATE TABLE `ip_blacklist`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip_address` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `description` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ip_address`(`ip_address` ASC) USING BTREE,
  INDEX `idx_ip`(`ip_address` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `nodes`;

CREATE TABLE `nodes`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `country` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `os` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `botnet_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_botnet_type`(`botnet_type` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 81 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `packet_loss_policy`;

CREATE TABLE `packet_loss_policy`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip_address` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `loss_rate` float NOT NULL,
  `description` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `enabled` tinyint(1) NULL DEFAULT 1,
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ip_address`(`ip_address` ASC) USING BTREE,
  INDEX `idx_ip`(`ip_address` ASC) USING BTREE,
  INDEX `idx_enabled`(`enabled` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `port_consume_task`;

CREATE TABLE `port_consume_task`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `task_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `target_ip` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `target_port` int NOT NULL,
  `threads` int NULL DEFAULT 100,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'running',
  `start_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `stop_time` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `task_id`(`task_id` ASC) USING BTREE,
  INDEX `idx_task_id`(`task_id` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `server_management`;

CREATE TABLE `server_management`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `location` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `ip` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `domain` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `os` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `Botnet_Name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '所控制的僵尸网络名称',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `socks4`;

CREATE TABLE `socks4`  (
  `id` int UNSIGNED NOT NULL,
  `port` smallint UNSIGNED NOT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = FIXED;

DROP TABLE IF EXISTS `syn_flood_task`;

CREATE TABLE `syn_flood_task`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `task_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `target_ip` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `target_port` int NOT NULL,
  `threads` int NULL DEFAULT 50,
  `duration` int NULL DEFAULT NULL,
  `rate` int NULL DEFAULT NULL,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'running',
  `start_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `stop_time` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `task_id`(`task_id` ASC) USING BTREE,
  INDEX `idx_task_id`(`task_id` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `tmp`;

CREATE TABLE `tmp`  (
  `id` int NULL DEFAULT NULL,
  `ip` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `time` varchar(25) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `command` varchar(3) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `detail` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `user_events`;

CREATE TABLE `user_events`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `event_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'admin',
  `ip` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `location` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `botnet_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `command` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'completed',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_event_time`(`event_time` ASC) USING BTREE,
  INDEX `idx_botnet_type`(`botnet_type` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 129 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS `users`;

CREATE TABLE `users`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` enum('管理员','操作员','访客') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_login` datetime NULL DEFAULT NULL,
  `status` enum('在线','离线') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '离线',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;


SET FOREIGN_KEY_CHECKS = 1;
