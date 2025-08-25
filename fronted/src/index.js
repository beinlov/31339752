import dva from 'dva';
import './utils/flexible';
import models from './models';
import router from './router';

// 1. Initialize
const app = dva();

// 2. Plugins
// app.use({});

// 3. Model
app.model(models.centerPage);
app.model(models.leftPage);
app.model(models.rightPage);
app.model(models.mapPosition);
app.model(models.mapState);

// 4. Router - Pass app to router
app.router(({ history }) => router({ history, app }));

// 5. Start
app.start('#root');

// Enable HMR for development
if (import.meta.hot) {
  import.meta.hot.accept();
}
