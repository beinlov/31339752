import React, { Fragment } from 'react';
import { Router, Route, Switch, Redirect } from 'dva/router';
import IndexPage from './components/IndexPage';
import LoginPage from './components/loginPage';
import AdminPage from './components/adminPage';
import { Iconstyle } from './assets/icon/iconfont';
import { Globalstyle } from './style/global';
import { Provider } from './utils/ModernConnect';

function RouterConfig({ history, app }) {
  // Ensure we have the store from the app
  const store = app._store;
  
  const route = () => {
    return (
      <Fragment>
        {/* 全局样式注册到界面中 */}
        <Iconstyle></Iconstyle>
        <Globalstyle></Globalstyle>

        {/* 使用现代 Context API 的 Provider */}
        <Provider store={store}>
          {/* 路由管理 */}
          <Switch>
            <Route path="/login" exact component={LoginPage} />
            <Route path="/index" exact component={IndexPage} />
            <Route path="/admin" exact component={AdminPage} />
            <Redirect from="/" to="/login" exact />
          </Switch>
        </Provider>
      </Fragment>
    );
  };

  return <Router history={history}>{route()}</Router>;
}

export default RouterConfig;
