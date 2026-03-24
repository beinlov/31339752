import React, { Fragment, useState } from 'react';
import { connect } from '../../../utils/ModernConnect';
import { 
  Typography,
  Box,
} from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import CleanupModal from '../../CleanupModal';

const useStyles = makeStyles((theme) => ({
  buttonContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.2rem',
    alignItems: 'center',
    position: 'absolute',
    top: '10%',  // 大幅上移避免与南海诸岛重叠
  },
  actionButton: {
    width: '1.4rem',  // 放大宽度
    height: '0.45rem',  // 放大高度
    padding: '0.05rem 0.08rem',
    backgroundColor: 'rgba(220, 50, 50, 0.85)',  // 红色背景
    border: '2px solid rgba(255, 100, 100, 0.9)',  // 红色边框
    borderRadius: '5px',
    cursor: 'pointer',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    transition: 'all 0.3s',
    boxShadow: '0 0 8px rgba(255, 50, 50, 0.5)',  // 红色发光
    '&:hover': {
      backgroundColor: 'rgba(240, 70, 70, 0.95)',  // hover时更亮的红色
      boxShadow: '0 0 15px rgba(255, 50, 50, 0.7)',
      borderColor: 'rgba(255, 120, 120, 1)',
    }
  },
  buttonText: {
    fontSize: '0.26rem',  // 放大字体
    fontWeight: 'bold',
    color: '#FFD700',  // 黄色文字
    textShadow: '0 0 8px rgba(255, 215, 0, 0.8), 0 0 3px rgba(0, 0, 0, 0.5)',  // 黄色光晕+黑色描边
    margin: 0,
    padding: 0,
  }
}));

const Takeover = ({ dispatch, selectedNetwork, botnetData }) => {
  const classes = useStyles();
  const [showCleanupModal, setShowCleanupModal] = useState(false);
  
  // 获取用户角色，判断是否有操作权限
  const userRole = localStorage.getItem('role');
  const canOperate = userRole === '管理员' || userRole === '操作员';  // 只有管理员和操作员可以操作
  const isGuest = userRole === '访客';  // 访客只能查看

  const handleClean = () => {
    // 打开清除模态框
    setShowCleanupModal(true);
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

      {/* 清除模态框 */}
      {showCleanupModal && (
        <CleanupModal 
          onClose={() => setShowCleanupModal(false)} 
          dispatch={dispatch}
          selectedNetwork={selectedNetwork}
        />
      )}
    </Fragment>
  );
};

const mapStateToProps = ({ mapState }) => ({
  selectedNetwork: mapState.selectedNetwork,
  botnetData: mapState.botnetData,
});

export default connect(mapStateToProps)(Takeover);