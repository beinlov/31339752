## 部署前准备

### 下载 IP 地理位置数据库
项目需要 IP 地理位置数据库文件，请按以下步骤获取：

1. 下载 IP_city_single_WGS84.awdb 文件
2. 放置到 `backend/ip_location/` 目录
3. 用U盘拷

### 需要进行修改的配置文件
backend/config.py 
backend/log_processor/config.py
backend/config_docker.py


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
