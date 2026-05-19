/**
 * 权限控制工具函数
 * 用于基于用户角色控制功能访问权限
 */

// 用户角色定义
export const USER_ROLES = {
  ADMIN: '管理员',
  OPERATOR: '操作员',
  GUEST: '访客'
};

// 权限检查函数
export const hasPermission = (userRole, requiredRole = USER_ROLES.ADMIN) => {
  // 只有admin用户有完全权限
  return userRole === USER_ROLES.ADMIN;
};

// 检查是否为只读用户（非admin用户）
export const isReadOnlyUser = (userRole) => {
  return userRole !== USER_ROLES.ADMIN;
};

// 获取当前用户角色
export const getCurrentUserRole = () => {
  return localStorage.getItem('role') || '';
};

// 获取当前用户名
export const getCurrentUsername = () => {
  return localStorage.getItem('username') || '';
};

// 检查当前用户是否有权限
export const currentUserHasPermission = (requiredRole = USER_ROLES.ADMIN) => {
  const currentRole = getCurrentUserRole();
  return hasPermission(currentRole, requiredRole);
};

// 检查当前用户是否为只读用户
export const isCurrentUserReadOnly = () => {
  return isReadOnlyUser(getCurrentUserRole());
};

// 权限控制的高阶组件
export const withPermissionCheck = (WrappedComponent, requiredRole = USER_ROLES.ADMIN) => {
  return function PermissionWrapper(props) {
    const hasAccess = currentUserHasPermission(requiredRole);
    
    if (!hasAccess) {
      return (
        <div style={{
          padding: '20px',
          textAlign: 'center',
          color: '#999',
          fontSize: '14px'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '10px' }}>🔒</div>
          <div>您没有权限访问此功能</div>
          <div style={{ fontSize: '12px', marginTop: '5px' }}>
            仅管理员可以使用此功能
          </div>
        </div>
      );
    }
    
    return <WrappedComponent {...props} />;
  };
};

// 按钮权限控制Hook
export const useButtonPermission = () => {
  const isReadOnly = isCurrentUserReadOnly();
  const currentRole = getCurrentUserRole();
  
  return {
    isDisabled: isReadOnly,
    tooltip: isReadOnly ? '仅管理员可使用此功能' : '',
    currentRole
  };
};
