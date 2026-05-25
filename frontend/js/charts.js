/**
 * CCAE 图表封装模块
 * 基于 Chart.js 封装，适配暗色主题
 */
const Charts = {
  // 图表实例存储
  instances: {},

  // 颜色配置（适配暗色主题）
  colors: {
    primary: '#3b82f6',
    success: '#22c55e',
    warning: '#eab308',
    danger: '#ef4444',
    muted: '#6b7280',
    // 调色板
    palette: [
      '#3b82f6', '#22c55e', '#eab308', '#ef4444',
      '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'
    ]
  },

  // 暗色主题默认配置
  darkTheme: {
    color: '#e5e7eb',
    gridColor: 'rgba(75, 85, 99, 0.3)',
    tooltipBg: 'rgba(17, 24, 39, 0.9)',
    tooltipText: '#e5e7eb'
  },

  /**
   * 销毁图表实例
   * @param {string} canvasId - Canvas 元素 ID
   */
  destroy(canvasId) {
    if (this.instances[canvasId]) {
      this.instances[canvasId].destroy();
      delete this.instances[canvasId];
    }
  },

  /**
   * 销毁所有图表实例
   */
  destroyAll() {
    Object.keys(this.instances).forEach(id => this.destroy(id));
  },

  /**
   * 获取调色板颜色
   * @param {number} index - 索引
   * @returns {string} 颜色值
   */
  getPaletteColor(index) {
    return this.colors.palette[index % this.colors.palette.length];
  },

  /**
   * 创建折线图
   * @param {string} canvasId - Canvas 元素 ID
   * @param {Array} labels - X 轴标签
   * @param {Array} datasets - 数据集数组 [{label, data, color?}]
   * @param {Object} options - 可选配置
   * @returns {Chart} 图表实例
   */
  line(canvasId, labels, datasets, options = {}) {
    this.destroy(canvasId);

    const ctx = document.getElementById(canvasId);
    if (!ctx) {
      console.error(`Canvas element not found: ${canvasId}`);
      return null;
    }

    const chartDatasets = datasets.map((ds, i) => ({
      label: ds.label || `数据集 ${i + 1}`,
      data: ds.data,
      borderColor: ds.color || this.getPaletteColor(i),
      backgroundColor: (ds.color || this.getPaletteColor(i)) + '20',
      fill: ds.fill !== false,
      tension: 0.4,
      pointRadius: 4,
      pointHoverRadius: 6
    }));

    const defaultOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: this.darkTheme.color }
        },
        tooltip: {
          backgroundColor: this.darkTheme.tooltipBg,
          titleColor: this.darkTheme.tooltipText,
          bodyColor: this.darkTheme.tooltipText
        }
      },
      scales: {
        x: {
          ticks: { color: this.darkTheme.color },
          grid: { color: this.darkTheme.gridColor }
        },
        y: {
          ticks: { color: this.darkTheme.color },
          grid: { color: this.darkTheme.gridColor }
        }
      }
    };

    this.instances[canvasId] = new Chart(ctx, {
      type: 'line',
      data: { labels, datasets: chartDatasets },
      options: { ...defaultOptions, ...options }
    });

    return this.instances[canvasId];
  },

  /**
   * 创建饼图
   * @param {string} canvasId - Canvas 元素 ID
   * @param {Array} labels - 标签数组
   * @param {Array} data - 数据数组
   * @param {Object} options - 可选配置
   * @returns {Chart} 图表实例
   */
  pie(canvasId, labels, data, options = {}) {
    this.destroy(canvasId);

    const ctx = document.getElementById(canvasId);
    if (!ctx) {
      console.error(`Canvas element not found: ${canvasId}`);
      return null;
    }

    const backgroundColors = labels.map((_, i) => this.getPaletteColor(i));

    const defaultOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { color: this.darkTheme.color }
        },
        tooltip: {
          backgroundColor: this.darkTheme.tooltipBg,
          titleColor: this.darkTheme.tooltipText,
          bodyColor: this.darkTheme.tooltipText
        }
      }
    };

    this.instances[canvasId] = new Chart(ctx, {
      type: 'pie',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: backgroundColors,
          borderColor: '#1f2937',
          borderWidth: 2
        }]
      },
      options: { ...defaultOptions, ...options }
    });

    return this.instances[canvasId];
  },

  /**
   * 创建条形图
   * @param {string} canvasId - Canvas 元素 ID
   * @param {Array} labels - X 轴标签
   * @param {Array} datasets - 数据集数组 [{label, data, color?}]
   * @param {Object} options - 可选配置
   * @returns {Chart} 图表实例
   */
  bar(canvasId, labels, datasets, options = {}) {
    this.destroy(canvasId);

    const ctx = document.getElementById(canvasId);
    if (!ctx) {
      console.error(`Canvas element not found: ${canvasId}`);
      return null;
    }

    const chartDatasets = datasets.map((ds, i) => ({
      label: ds.label || `数据集 ${i + 1}`,
      data: ds.data,
      backgroundColor: (ds.color || this.getPaletteColor(i)) + 'cc',
      borderColor: ds.color || this.getPaletteColor(i),
      borderWidth: 1,
      borderRadius: 4
    }));

    const defaultOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: this.darkTheme.color }
        },
        tooltip: {
          backgroundColor: this.darkTheme.tooltipBg,
          titleColor: this.darkTheme.tooltipText,
          bodyColor: this.darkTheme.tooltipText
        }
      },
      scales: {
        x: {
          ticks: { color: this.darkTheme.color },
          grid: { color: this.darkTheme.gridColor }
        },
        y: {
          ticks: { color: this.darkTheme.color },
          grid: { color: this.darkTheme.gridColor }
        }
      }
    };

    this.instances[canvasId] = new Chart(ctx, {
      type: 'bar',
      data: { labels, datasets: chartDatasets },
      options: { ...defaultOptions, ...options }
    });

    return this.instances[canvasId];
  },

  /**
   * 更新图表数据
   * @param {string} canvasId - Canvas 元素 ID
   * @param {Object} newData - 新数据 {labels?, datasets?}
   */
  update(canvasId, newData) {
    const chart = this.instances[canvasId];
    if (!chart) {
      console.error(`Chart instance not found: ${canvasId}`);
      return;
    }

    if (newData.labels) {
      chart.data.labels = newData.labels;
    }
    if (newData.datasets) {
      newData.datasets.forEach((ds, i) => {
        if (chart.data.datasets[i]) {
          chart.data.datasets[i].data = ds.data;
          if (ds.label) chart.data.datasets[i].label = ds.label;
        }
      });
    }
    chart.update();
  }
};
