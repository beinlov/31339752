import React, { PureComponent, Fragment } from 'react';
import { formatTime } from '../../utils';
import {
  Decoration10,
  Decoration8,
  Decoration6,
  Loading
} from '@jiaminghi/data-view-react';
import { withRouter } from 'dva/router';

import { TopBox, TimeBox, BackButton } from './style';

class TopPage extends PureComponent {
  constructor(props) {
    super(props);
    this.state = {
      title: '接管的僵尸网络展示处置平台',
      timeStr: '',
      dateStr: '',
      weekDay: '',
      loading: true,
      weekday: [
        '星期天',
        '星期一',
        '星期二',
        '星期三',
        '星期四',
        '星期五',
        '星期六',
      ],
    };
  }

  componentDidMount() {
    // Initial time update
    this.updateTime();
    // Set loading to false after a short delay
    setTimeout(() => {
      this.setState({ loading: false });
    }, 1000);
    // Set up time interval
    this.setTimingFn();
  }

  componentWillUnmount() {
    // Clear interval when component unmounts
    if (this.timing) {
      clearInterval(this.timing);
    }
  }

  updateTime() {
    const dateStr = formatTime(new Date(), 'yyyy-MM-dd');
    const timeStr = formatTime(new Date(), 'HH:mm:ss');
    const weekDay = this.state.weekday[new Date().getDay()];
    
    this.setState({
      dateStr,
      timeStr,
      weekDay
    });
  }

  setTimingFn() {
    this.timing = setInterval(() => {
      this.updateTime();
    }, 1000);
  }

  handleBackClick = () => {
    // 跳转回后台管理系统
    this.props.history.push('/admin');
  }

  render() {
    const { title, dateStr, timeStr, weekDay, loading } = this.state;
    
    // 获取用户角色
    const userRole = localStorage.getItem('role');
    const isAdmin = userRole === '管理员';
    
    if (loading) {
      return (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100%' 
        }}>
          <Loading style={{ width: '150px', height: '150px' }} />
        </div>
      );
    }

    return (
      <Fragment>
        <TopBox>
          <div className='top_box'>
            <Decoration10 className='top_decoration10' />
            <div className='title-box'>
              <Decoration8
                className='top_decoration8'
                color={['#568aea', '#000000']}
              />
              <div className='title'>
                <span className='title-text'>{title}</span>
                <Decoration6
                  className='title-bototm top_decoration6'
                  reverse={true}
                  color={['#50e3c2', '#67a1e5']}
                />
              </div>

              <Decoration8
                reverse={true}
                className='top_decoration8'
                color={['#568aea', '#000000']}
              />
            </div>
            <Decoration10 className='top_decoration10 top_decoration10_reverse' />
            {/* 只有管理员才显示返回按钮 */}
            {isAdmin && (
              <BackButton onClick={this.handleBackClick}>
                <span className='back-icon'>←</span>
                <span className='back-text'>返回</span>
              </BackButton>
            )}
            <TimeBox>
              <h3>{dateStr}</h3>
              <h3>{timeStr} {weekDay}</h3>
            </TimeBox>
          </div>
        </TopBox>
      </Fragment>
    );
  }
}

export default withRouter(TopPage);
