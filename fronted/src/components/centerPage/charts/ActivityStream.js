import React, { PureComponent } from 'react';
import { userOptions } from './options';
import { ScrollBoard } from '@jiaminghi/data-view-react';
import request from '../../../utils/request';
import { getApiUrl } from '../../../config/api';


class UserSituation extends PureComponent {
  constructor(props) {
    super(props);
    this.containerRef = React.createRef();
    this.state = {
      userEvents: null,
      config: {
        headerBGC: 'rgba(0, 21, 41, 0.4)',
        oddRowBGC: 'rgba(0, 40, 70, 0.3)',
        evenRowBGC: 'rgba(0, 21, 41, 0.3)',
        index: false,
        columnWidth: [],
        align: ['center', 'center', 'center', 'center', 'center'],
        rowNum: 4,
        headerHeight: 60,
        rowHeight: 70,
        waitTime: 2000,
        carousel: 'single',
        hoverPause: true,
        scroll: false,
        loop: false,
        headerFontSize: 22,
        rowFontSize: 20,
        headerFontFamily: '"Microsoft YaHei", sans-serif',
        rowFontFamily: '"Microsoft YaHei", sans-serif',
        textAlign: 'center',
        headerColor: '#00EAFF',
        rowColor: '#FFFFFF'
      },
    };
  }

  componentDidMount() {
    this.fetchUserEvents();
    this.timer = setInterval(this.fetchUserEvents, 30000);
    
    // 使用 ResizeObserver 监听容器大小变化
    this.resizeObserver = new ResizeObserver(() => {
      this.updateColumnWidth();
    });
    
    if (this.containerRef.current) {
      this.resizeObserver.observe(this.containerRef.current);
    }
  }

  componentDidUpdate(prevProps) {
    if (prevProps.selectedNetwork !== this.props.selectedNetwork) {
      this.fetchUserEvents();
    }
  }

  componentWillUnmount() {
    if (this.timer) {
      clearInterval(this.timer);
    }
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
  }

  updateColumnWidth = () => {
    if (this.containerRef.current) {
      const width = this.containerRef.current.clientWidth;
      const colWidth = Math.floor(width / 5);
      this.setState(prevState => ({
        config: {
          ...prevState.config,
          columnWidth: [colWidth, colWidth, colWidth, colWidth, colWidth]
        }
      }));
    }
  };

  fetchUserEvents = async () => {
    try {
      const { selectedNetwork } = this.props;
      const botnetType = (selectedNetwork || 'asruex').toString().trim().toLowerCase();
      const response = await request(getApiUrl(`/api/active-botnet-communications?botnet_type=${botnetType}`));

      const rows = Array.isArray(response)
        ? response
        : (response && Array.isArray(response.data) ? response.data : []);

      // DEBUG: 打印接收到的数据
      console.log('[ActivityStream] Received rows:', rows.length);
      if (rows.length > 0) {
        console.log('[ActivityStream] First row:', rows[0]);
        console.log('[ActivityStream] First row keys:', Object.keys(rows[0]));
        console.log('[ActivityStream] province:', rows[0].province);
        console.log('[ActivityStream] city:', rows[0].city);
      }

      const formattedData = rows.map(event => {
        // 根据 status 显示节点状态
        let statusText = '未知';
        let statusColor = '#999999';
        if (event.status === 'active') {
          statusText = '在线';
          statusColor = '#00FF7F';
        } else if (event.status === 'cleaned') {
          statusText = '已清除';
          statusColor = '#FFA500';
        }
        
        // 构建地区信息：country + province + city
        const locationParts = [];
        if (event.country) locationParts.push(event.country);
        if (event.province) locationParts.push(event.province);
        if (event.city) locationParts.push(event.city);
        const location = locationParts.join(' ') || '-';
        
        // DEBUG: 打印地区信息构建过程
        if (rows.indexOf(event) === 0) {  // 只打印第一条
          console.log('[ActivityStream] Building location for first row:');
          console.log('  event.country:', event.country);
          console.log('  event.province:', event.province);
          console.log('  event.city:', event.city);
          console.log('  locationParts:', locationParts);
          console.log('  location:', location);
        }
        
        // 单位逻辑：如果有 unit 数据就显示，否则显示地区信息
        const unit = event.unit || location;
        
        return [
          `<span style="color: #00EAFF; font-weight: bold;">${event.time}</span>`,
          `<span style="color: #ffffff; font-weight: bold;">${event.ip}</span>`,
          `<span style="color: #00EAFF; font-weight: bold;">${location}</span>`,
          `<span style="color: ${statusColor}; font-weight: bold;">${statusText}</span>`,
          `<span style="color: #FFD700; font-weight: bold;">${unit}</span>`
        ];
      });
      
      this.setState(prevState => ({
        userEvents: formattedData,
        config: {
          ...prevState.config,
          scroll: formattedData.length > 4,
          loop: formattedData.length > 4
        }
      }));
    } catch (error) {
      console.error('获取活跃僵尸节点通信数据失败:', error);
      this.setState(prevState => ({
        userEvents: [],
        config: {
          ...prevState.config,
          scroll: false,
          loop: false
        }
      }));
    }
  };

  render() {
    const { config, userEvents } = this.state;

    const scrollBoardConfig = {
      ...config,
      ...userOptions(userEvents)
    };

    return (
      <div className="user-situation-container">
        <div className="user-situation-title">
          <i className="iconfont" style={{ marginRight: '8px', fontSize: '18px' }}>&#xe7fd;</i>
          已知僵尸节点动态展示
        </div>
        <div className="user-situation-content" ref={this.containerRef}>
          {userEvents ? (
            <ScrollBoard
              config={scrollBoardConfig}
              style={{
                width: '100%',
                height: '100%',
                borderRadius: '4px',
                overflow: 'hidden',
                boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)'
              }}
            />
          ) : (
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              height: '100%',
              color: '#BCDCFF',
              fontSize: '14px'
            }}>
              <div className="loading-spinner"></div>
              加载中...
            </div>
          )}
        </div>
      </div>
    );
  }
}

export default UserSituation; 