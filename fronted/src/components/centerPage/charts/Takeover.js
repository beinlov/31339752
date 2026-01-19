import React, { Fragment } from 'react';
import { connect } from '../../../utils/ModernConnect';
import { 
  Typography,
  Box,
} from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import { getUserLocation } from '../../../utils/index';

const useStyles = makeStyles((theme) => ({
  buttonContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.2rem',
    alignItems: 'center',
    position: 'absolute',
    top: '25%',
  },
  actionButton: {
    width: '1rem',
    height: '0.3rem',
    padding: '0.03rem 0.03rem',
    backgroundColor: 'rgba(19, 25, 47, 0.8)',
    borderRadius: '5px',
    cursor: 'pointer',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    transition: 'all 0.3s',
    '&:hover': {
      backgroundColor: 'rgba(29, 35, 57, 0.9)',
      boxShadow: '0 0 10px rgba(0, 100, 250, 0.5)',
    }
  },
  buttonText: {
    fontSize: '0.2rem',
    fontWeight: 'bold',
    color: '#89e5ff',
    textShadow: '0 0 5px rgba(77, 182, 229, 0.5)',
    margin: 0,
    padding: 0,
  }
}));

const Takeover = ({ dispatch, selectedNetwork, botnetData }) => {
  const classes = useStyles();
  
  // 获取用户角色，判断是否有操作权限
  const userRole = localStorage.getItem('role');
  const canOperate = userRole === '管理员' || userRole === '操作员';  // 只有管理员和操作员可以操作
  const isGuest = userRole === '访客';  // 访客只能查看

  const handleClean = async () => {
    if (!selectedNetwork) {
      console.error('No botnet network selected');
      return;
    }

    // 使用 handleFlyLines effect
    dispatch({
      type: 'mapState/handleFlyLines'
    });

    try {
      // 获取操作者的IP地理位置
      const locationInfo = await getUserLocation();
      console.log('操作者IP地理位置:', locationInfo);

      // 调用清除API
      const token = localStorage.getItem('token');
      fetch('http://localhost:8000/api/clean-botnet', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          botnet_type: selectedNetwork,  // 使用选中的僵尸网络类型
          target_machines: [],    // 空数组表示清除所有节点
          clean_method: 'clear',  // 有效的清除方法之一
          username: localStorage.getItem('username') || 'admin',
          location: locationInfo.location,
          operator_ip: locationInfo.ip
        }),
      })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          // 更新数据显示
          dispatch({
            type: 'mapState/fetchProvinceAmounts'
          });
          dispatch({
            type: 'mapState/fetchBotnetDistribution'
          });
        }
      })
      .catch(error => {
        console.error('Error:', error);
      });
    } catch (error) {
      console.error('Error getting location:', error);
    }
  };

  return (
    <Fragment>
      <Box className={classes.buttonContainer}>
        <Box 
          className={classes.actionButton}
          onClick={canOperate ? handleClean : undefined}
          style={{ 
            opacity: canOperate ? 1 : 0.5, 
            cursor: canOperate ? 'pointer' : 'not-allowed',
            pointerEvents: canOperate ? 'auto' : 'none'
          }}
          title={isGuest ? '访客无操作权限' : ''}
        >
          <Typography className={classes.buttonText}>
            一键清除
          </Typography>
        </Box>

      </Box>
    </Fragment>
  );
};

const mapStateToProps = ({ mapState }) => ({
  selectedNetwork: mapState.selectedNetwork,
  botnetData: mapState.botnetData,
});

export default connect(mapStateToProps)(Takeover);