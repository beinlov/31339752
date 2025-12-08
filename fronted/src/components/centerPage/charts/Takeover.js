import React, { useState, Fragment } from 'react';
import { connect } from '../../../utils/ModernConnect';
import { 
  Typography,
  Box,
  Switch,
  FormGroup,
  FormControlLabel,
} from '@material-ui/core';
import Draggable from 'react-draggable';
import { makeStyles } from '@material-ui/core/styles';
import { getUserLocation } from '../../../utils/index';

const useStyles = makeStyles((theme) => ({
  buttonContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.2rem',
    alignItems: 'center',
    position: 'absolute',
    //top: '0%',
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
  },
  dialogBackdrop: {
    position: 'fixed',
    top: 0,
    left: 0,
    width: '100vw',
    height: '100vh',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1300,
  },
  dialogContainer: {
    width: '25vw',
    height: '22vw',
    backgroundColor: '#13192f',
    border: '1px solid #89e5ff',
    borderRadius: '4px',
    boxShadow: '0 0 10px rgba(0, 0, 0, 0.5)',
    display: 'flex',
    flexDirection: 'column',
    color: '#fff',
  },
  dialogTitle: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#1d2339',
    padding: '8px 12px',
    cursor: 'move',
    borderBottom: '1px solid rgba(137, 229, 255, 0.3)',
    borderRadius: '4px 4px 0 0',
    width: '100%',
    height: '15%',
  },
  titleText: {
    fontSize: '0.22rem',
    color: '#89e5ff',
    fontWeight: 'normal',
    margin: 0,
  },
  closeButton: {
    color: '#89e5ff',
    padding: '4px',
    cursor: 'pointer',
    borderRadius: '2px',
    '&:hover': {
      backgroundColor: 'rgba(137, 229, 255, 0.1)',
    },
  },
  dialogContent: {
    padding: '12px 15px',
    backgroundColor: '#13192f',
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
  },
  switchLabel: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    marginBottom: '8px',
    '&:last-child': {
      marginBottom: 0,
    },
    '& .MuiFormControlLabel-label': {
      fontSize: '0.22rem',
      color: '#fff',
      fontWeight: 'normal',
      marginRight: '10px',
      flex: 1,
    },
    '& .MuiSwitch-root': {
      transform: 'scale(0.7)',
      '& .MuiSwitch-track': {
        backgroundColor: 'rgba(137, 229, 255, 0.3)',
        opacity: 1,
      },
      '& .MuiSwitch-thumb': {
        backgroundColor: '#89e5ff',
        boxShadow: '0 0 3px rgba(137, 229, 255, 0.3)',
      },
      '& .Mui-checked': {
        '& + .MuiSwitch-track': {
          backgroundColor: 'rgba(137, 229, 255, 0.6) !important',
          opacity: 1,
        },
        '& .MuiSwitch-thumb': {
          backgroundColor: '#89e5ff',
        }
      }
    }
  },
  formGroup: {
    width: '100%',
  }
}));

// 可拖拽的自定义弹窗组件
function DraggableDialog({ open, onClose, children }) {
  if (!open) return null;
  
  return (
    <Draggable handle=".draggable-title" bounds="body">
      <div>
        {children}
      </div>
    </Draggable>
  );
}

const Takeover = ({ dispatch, selectedNetwork, botnetData }) => {
  const classes = useStyles();
  const [openSettings, setOpenSettings] = useState(false);
  const [internalAntiTrace, setInternalAntiTrace] = useState(false);
  const [externalAntiTrace, setExternalAntiTrace] = useState(false);
  
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

  const handleReuse = () => {
    // 处理设置逻辑
    setOpenSettings(true);
  };

  const handleRangeClean = async () => {
    if (!selectedNetwork) {
      console.error('No botnet network selected');
      return;
    }

    try {
      const locationInfo = await getUserLocation();
      
      // 这里可以添加一个弹窗让用户选择要清理的IP范围
      const targetMachines = []; // 这里应该从用户选择中获取

      const token = localStorage.getItem('token');
      fetch('http://localhost:8000/api/clean-botnet', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          botnet_type: selectedNetwork,
          target_machines: targetMachines,
          clean_method: 'clear',
          username: localStorage.getItem('username') || 'admin',
          location: locationInfo.location,
          operator_ip: locationInfo.ip
        }),
      })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
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
      console.error('Error:', error);
    }
  };

  const handleSuppress = async () => {
    if (!selectedNetwork) {
      console.error('No botnet network selected');
      return;
    }

    try {
      const locationInfo = await getUserLocation();
      
      const token = localStorage.getItem('token');
      fetch('http://localhost:8000/api/clean-botnet', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          botnet_type: selectedNetwork,
          target_machines: [],
          clean_method: 'suppress',
          username: localStorage.getItem('username') || 'admin',
          location: locationInfo.location,
          operator_ip: locationInfo.ip
        }),
      })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
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
      console.error('Error:', error);
    }
  };

  const handleCloseSettings = () => {
    setOpenSettings(false);
  };

  const handleInternalAntiTraceChange = (event) => {
    setInternalAntiTrace(event.target.checked);
    // 这里可以添加更多处理逻辑
  };

  const handleExternalAntiTraceChange = (event) => {
    setExternalAntiTrace(event.target.checked);
    // 这里可以添加更多处理逻辑
  };

  return (
    <Fragment>
      <Box className={classes.buttonContainer}>
        <Box 
          className={classes.actionButton}
          onClick={canOperate ? handleSuppress : undefined}
          style={{ 
            opacity: canOperate ? 1 : 0.5, 
            cursor: canOperate ? 'pointer' : 'not-allowed',
            pointerEvents: canOperate ? 'auto' : 'none'
          }}
          title={isGuest ? '访客无操作权限' : ''}
        >
          <Typography className={classes.buttonText}>
            抑制阻断
          </Typography>
        </Box>

        <Box 
          className={classes.actionButton}
          onClick={canOperate ? handleRangeClean : undefined}
          style={{ 
            opacity: canOperate ? 1 : 0.5, 
            cursor: canOperate ? 'pointer' : 'not-allowed',
            pointerEvents: canOperate ? 'auto' : 'none'
          }}
          title={isGuest ? '访客无操作权限' : ''}
        >
          <Typography className={classes.buttonText}>
            范围清除
          </Typography>
        </Box> 
        
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

        <Box 
          className={classes.actionButton}
          onClick={canOperate ? handleReuse : undefined}
          style={{ 
            opacity: canOperate ? 1 : 0.5, 
            cursor: canOperate ? 'pointer' : 'not-allowed',
            pointerEvents: canOperate ? 'auto' : 'none'
          }}
          title={isGuest ? '访客无操作权限' : ''}
        >
          <Typography className={classes.buttonText}>
            设置
          </Typography>
        </Box>
      </Box>

      {openSettings && (
        <div className={classes.dialogBackdrop} onClick={handleCloseSettings}>
          <DraggableDialog open={openSettings} onClose={handleCloseSettings}>
            <div 
              className={classes.dialogContainer}
              onClick={(e) => e.stopPropagation()}
            >
              <div className={`${classes.dialogTitle} draggable-title`}>
                <div className={classes.titleText}>设置</div>
                <div 
                  className={classes.closeButton}
                  onClick={handleCloseSettings}
                >
                  ✕
                </div>
              </div>
              <div className={classes.dialogContent}>
                <FormGroup className={classes.formGroup}>
                  <FormControlLabel
                    className={classes.switchLabel}
                    labelPlacement="start"
                    control={
                      <Switch
                        checked={internalAntiTrace}
                        onChange={handleInternalAntiTraceChange}
                        color="primary"
                      />
                    }
                    label="启用内置反溯源"
                  />
                  <FormControlLabel
                    className={classes.switchLabel}
                    labelPlacement="start"
                    control={
                      <Switch
                        checked={externalAntiTrace}
                        onChange={handleExternalAntiTraceChange}
                        color="primary"
                      />
                    }
                    label="启用对方反溯源"
                  />
                </FormGroup>
              </div>
            </div>
          </DraggableDialog>
        </div>
      )}
    </Fragment>
  );
};

const mapStateToProps = ({ mapState }) => ({
  selectedNetwork: mapState.selectedNetwork,
  botnetData: mapState.botnetData,
});

export default connect(mapStateToProps)(Takeover);