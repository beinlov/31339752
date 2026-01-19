## 部署前准备

### 下载 IP 地理位置数据库
项目需要 IP 地理位置数据库文件，请按以下步骤获取：

1. 下载 IP_city_single_WGS84.awdb 文件
2. 放置到 `backend/ip_location/` 目录
3. 用U盘拷

### 配置文件说明（修改数据库密码等操作）

**✅ 配置已统一！现在只需修改一个配置文件！**

- **非Docker环境**: 只需修改 `backend/config.py`
- **Docker环境**: 只需修改 `backend/config_docker.py` 或使用环境变量

详细配置指南请查看：[CONFIG_GUIDE.md](CONFIG_GUIDE.md)

> ⚠️ 注意：`backend/log_processor/config.py` 已弃用，所有配置已统一到 `backend/config.py`

### 关于数据库
详见backend/migrations目录
通过编写脚本实现数据库的改动
有以下三个使用场景：
1.新成员初始化数据库
2.需要修改数据库：按照目录指示编写迁移文件
3.同步其他人的数据库变更：运行迁移文件

### 代码编写规范
1.ai生成的文件如果觉得有必要留存，请把md文件放进backend/debugging,把测试脚本放进test文件夹
2.把自己进行的改动放到根目录下的change.md，最好自己写

### Github使用规范
按照CodeGuide.md中的流程进行代码提交和协作。
详细流程请参考CodeGuide.md文件。

