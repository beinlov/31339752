import React, { PureComponent } from 'react';
import Chart from '../../../components/chart';
import { IndustryDistributionOptions } from './options';
import request from '../../../utils/request';
import { getApiUrl } from '../../../config/api';

class IndustryDistribution extends PureComponent {
  constructor(props) {
    super(props);
    this.state = {
      renderer: 'canvas',
      industryData: null
    };
  }

  componentDidMount() {
    this.fetchIndustryData();
  }

  fetchIndustryData = async () => {
    try {
      const response = await request(getApiUrl('/api/industry-distribution'));
      if (response && response.data) {
        // 将数据转换为饼图所需格式
        const formattedData = response.data.map(item => ({
          name: item.name,
          value: item.value
        }));
        this.setState({ industryData: formattedData });
      }
    } catch (error) {
      console.error('获取行业分布数据失败:', error);
    }
  };

  render() {
    const { renderer, industryData } = this.state;
    return (
      <div style={{ width: '100%', height: '100%' }}>
        {industryData ? (
          <Chart
            renderer={renderer}
            option={IndustryDistributionOptions({ data: industryData })}
          />
        ) : (
          ''
        )}
      </div>
    );
  }
}

export default IndustryDistribution; 