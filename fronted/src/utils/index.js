export function debounce(func, wait, immediate) {
  let timeout, args, context, timestamp, result;

  const later = function () {
    // 据上一次触发时间间隔
    const last = +new Date() - timestamp;

    // 上次被包装函数被调用时间间隔 last 小于设定时间间隔 wait
    if (last < wait && last > 0) {
      timeout = setTimeout(later, wait - last);
    } else {
      timeout = null;
      // 如果设定为immediate===true，因为开始边界已经调用过了此处无需调用
      if (!immediate) {
        result = func.apply(context, args);
        if (!timeout) context = args = null;
      }
    }
  };

  return function (...args) {
    context = this;
    timestamp = +new Date();
    const callNow = immediate && !timeout;
    // 如果延时不存在，重新设定延时
    if (!timeout) timeout = setTimeout(later, wait);
    if (callNow) {
      result = func.apply(context, args);
      context = args = null;
    }

    return result;
  };
}

/**
 * @param {date} time 需要转换的时间
 * @param {String} fmt 需要转换的格式 如 yyyy-MM-dd、yyyy-MM-dd HH:mm:ss
 */
export function formatTime(time, fmt) {
  if (!time) return '';
  else {
    const date = new Date(time);
    const o = {
      'M+': date.getMonth() + 1,
      'd+': date.getDate(),
      'H+': date.getHours(),
      'm+': date.getMinutes(),
      's+': date.getSeconds(),
      'q+': Math.floor((date.getMonth() + 3) / 3),
      S: date.getMilliseconds(),
    };
    if (/(y+)/.test(fmt))
      fmt = fmt.replace(
        RegExp.$1,
        (date.getFullYear() + '').substr(4 - RegExp.$1.length)
      );
    for (const k in o) {
      if (new RegExp('(' + k + ')').test(fmt)) {
        fmt = fmt.replace(
          RegExp.$1,
          RegExp.$1.length === 1
            ? o[k]
            : ('00' + o[k]).substr(('' + o[k]).length)
        );
      }
    }
    return fmt;
  }
}

/**
 *
 * @param {number} len 随机字符串的长度
 */
export function randomString(len) {
  len = len || 32;
  let $chars =
    'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678'; /****默认去掉了容易混淆的字符oOLl,9gq,Vv,Uu,I1****/
  let maxPos = $chars.length;
  let pwd = '';
  for (let i = 0; i < len; i++) {
    pwd += $chars.charAt(Math.floor(Math.random() * maxPos));
  }
  return pwd;
}

/**
 * 每三个数字加逗号，位数刚好是 3 的倍数头部不会加逗号
 * @param {number & !0XXXX} num 需要格式化的数字,不能以 0 开头
 */

export function toThousands(num) {
  let result = '';
  num = (num || 0).toString();
  while (num.length > 3) {
    result = ',' + num.slice(-3) + result;
    num = num.slice(0, num.length - 3);
  }
  if (num) {
    result = num + result;
  }
  return result;
}

export const getUserLocation = async () => {
  try {
    // 尝试多个获取IP的API
    const ipApis = [
      // 'https://api.ipify.org?format=json',
      // 'https://api.myip.la/json',
      // 'https://api.ip.sb/jsonip',
      'https://myip.ipip.net/json'  // 国内可访问
    ];

    let realIP = null;
    for (const api of ipApis) {
      try {
        const ipResponse = await fetch(api);
        const ipData = await ipResponse.json();
        // 不同API返回格式不同，需要适配
        realIP = ipData.ip || ipData.data?.ip || ipData.clientIP;
        if (realIP) break;
      } catch (error) {
        console.warn(`IP API ${api} 调用失败:`, error);
        continue;
      }
    }

    if (!realIP) {
      // 如果所有API都失败了，使用后端获取
      const response = await fetch('http://localhost:8000/api/ip-location', {
        method: 'GET',
        credentials: 'include'
      });
      const data = await response.json();
      return {
        ip: data.ip,
        city: data.city || '未知城市',
        country: data.country,
        location: data.city || data.location,  // 优先使用城市作为位置
        isp: data.isp,
        source: 'backend'
      };
    }

    // 使用获取到的IP调用后端地理位置API
    const response = await fetch('http://localhost:8000/api/ip-location', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ ip: realIP })
    });
    
    if (!response.ok) {
      throw new Error('获取位置信息失败');
    }

    const data = await response.json();
    console.log('IP地理位置信息:', data);

    return {
      ip: realIP,
      city: data.city || '未知城市',
      country: data.country,
      location: data.city || data.location,  // 优先使用城市作为位置
      isp: data.isp,
      source: 'ip_apis'
    };
    
  } catch (error) {
    console.error('获取用户位置信息失败:', error);
    return { 
      ip: '未知', 
      city: '未知城市', 
      country: '未知国家', 
      location: '未知城市',  // 使用城市作为默认位置
      isp: '未知ISP',
      source: 'error'
    };
  }
};

// 添加 delay 函数
export const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));
