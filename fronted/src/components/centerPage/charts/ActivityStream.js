import React, { PureComponent } from 'react';
import { userOptions } from './options';
import { ScrollBoard } from '@jiaminghi/data-view-react';
import request from '../../../utils/request';

// 添加命令转换函数和对应的颜色
const commandConfig = {
  'clear': { text: '清除节点', color: '#FF6B6B' },
  'reuse': { text: '节点再利用', color: '#4ECDC4' },
  'ddos': { text: 'DDos攻击', color: '#FFD93D' },
  'suppress': { text: '抑制阻断', color: '#6C5CE7' }
};

const translateCommand = (command) => {
  for (const [key, value] of Object.entries(commandConfig)) {
    if (command.includes(key)) return `<span style="color: ${value.color}">${value.text}</span>`;
  }
  return command;
};

class UserSituation extends PureComponent {
  constructor(props) {
    super(props);
    this.state = {
      userEvents: null,
      config: {
        headerBGC: 'rgba(15, 19, 37, 0.6)',
        oddRowBGC: 'rgba(15, 19, 37, 0.4)',
        evenRowBGC: 'rgba(23, 28, 51, 0.4)',
        index: false,
        columnWidth: [],
        align: ['center'],
        rowNum: 5,
        headerHeight: 40,
        rowHeight: 45,
        waitTime: 2500,
        carousel: 'single',
        hoverPause: true,
        scroll: false,
        loop: false,
        headerFontSize: 14,
        rowFontSize: 14,
        headerFontFamily: '"Microsoft YaHei", sans-serif',
        rowFontFamily: '"Microsoft YaHei", sans-serif',
        textAlign: 'center',
        headerColor: '#BCDCFF',
        rowColor: '#E6EFF8'
      },
    };
  }

  componentDidMount() {
    this.fetchUserEvents();
    this.timer = setInterval(this.fetchUserEvents, 30000);
  }

  componentWillUnmount() {
    if (this.timer) {
      clearInterval(this.timer);
    }
  }

  fetchUserEvents = async () => {
    try {
      const response = await request('http://localhost:8000/api/user-events');
      if (Array.isArray(response)) {
        const formattedData = response.map(event => [
          `<span style="color: #BCDCFF">${event.time}</span>`,
          `<span style="color: #4FACFE">${event.ip}</span>`,
          `<span style="color: #E6EFF8">${event.location}</span>`,
          translateCommand(event.command)
        ]);
        
        this.setState(prevState => ({
          userEvents: formattedData,
          config: {
            ...prevState.config,
            scroll: formattedData.length > 5,
            loop: formattedData.length > 5
          }
        }));
      }
    } catch (error) {
      console.error('获取用户事件数据失败:', error);
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
          清除处理事件动态
        </div>
        <div className="user-situation-content">
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