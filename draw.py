import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import scienceplots  # 需要安装: pip install SciencePlots

# 设置科研论文样式
#plt.style.use(['science', 'ieee', 'grid'])  # IEEE期刊样式
plt.style.use('default')

# 创建数据（基于之前讨论的参数）
dimensions = [16, 32, 64, 128, 256]
f1_scores_dim = [94.5, 97.8, 99.0, 98.9, 98.7]  # 嵌入维度对F1分数的影响

layers = [1, 2, 3, 4]
f1_scores_layers = [95.2, 98.0, 99.0, 98.2]  # GAT层数对F1分数的影响

mask_rates = [0.3, 0.5, 0.7]
f1_scores_mask = [96.5, 99.0, 95.8]  # 掩码率对F1分数的影响

# 创建子图
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# 配置颜色方案（使用Seaborn的学术调色板）
colors = sns.color_palette("husl", 3)

# 图表1：嵌入维度敏感性分析
axes[0].plot(dimensions, f1_scores_dim, 
            marker='o', 
            linewidth=2.5, 
            markersize=8,
            color=colors[0],
            label='F1-Score')

# 标记最佳点
best_dim_idx = f1_scores_dim.index(max(f1_scores_dim))
axes[0].plot(dimensions[best_dim_idx], f1_scores_dim[best_dim_idx], 
            'o', 
            markersize=12, 
            markerfacecolor='none',
            markeredgecolor='red', 
            markeredgewidth=2,
            label='Optimal Point (d=64)')

axes[0].set_xlabel('Embedding Dimension (d)', fontsize=12, fontweight='bold')
axes[0].set_ylabel('F1-Score (%)', fontsize=12, fontweight='bold')
axes[0].set_title('(a) Embedding Dimension Sensitivity', fontsize=13, fontweight='bold')
axes[0].set_ylim(92, 100)
axes[0].grid(True, alpha=0.3)
axes[0].legend()

# 图表2：GAT层数敏感性分析
axes[1].plot(layers, f1_scores_layers, 
            marker='s', 
            linewidth=2.5, 
            markersize=8,
            color=colors[1],
            label='F1-Score')

# 标记最佳点
best_layer_idx = f1_scores_layers.index(max(f1_scores_layers))
axes[1].plot(layers[best_layer_idx], f1_scores_layers[best_layer_idx], 
            's', 
            markersize=12, 
            markerfacecolor='none',
            markeredgecolor='red', 
            markeredgewidth=2,
            label='Optimal Point (l=3)')

axes[1].set_xlabel('GAT Layers (l)', fontsize=12, fontweight='bold')
axes[1].set_ylabel('F1-Score (%)', fontsize=12, fontweight='bold')
axes[1].set_title('(b) GAT Layers Sensitivity', fontsize=13, fontweight='bold')
axes[1].set_ylim(92, 100)
axes[1].grid(True, alpha=0.3)
axes[1].legend()

# 图表3：掩码率敏感性分析
axes[2].plot(mask_rates, f1_scores_mask, 
            marker='^', 
            linewidth=2.5, 
            markersize=8,
            color=colors[2],
            label='F1-Score')

# 标记最佳点
best_mask_idx = f1_scores_mask.index(max(f1_scores_mask))
axes[2].plot(mask_rates[best_mask_idx], f1_scores_mask[best_mask_idx], 
            '^', 
            markersize=12, 
            markerfacecolor='none',
            markeredgecolor='red', 
            markeredgewidth=2,
            label='Optimal Point (r=0.5)')

axes[2].set_xlabel('Masking Rate (r)', fontsize=12, fontweight='bold')
axes[2].set_ylabel('F1-Score (%)', fontsize=12, fontweight='bold')
axes[2].set_title('(c) Masking Rate Sensitivity', fontsize=13, fontweight='bold')
axes[2].set_ylim(92, 100)
axes[2].grid(True, alpha=0.3)
axes[2].legend()

# 调整布局
plt.tight_layout()

# 保存为高质量图片（适合论文发表）
plt.savefig('hyperparameter_sensitivity_analysis.png', 
           dpi=300, 
           bbox_inches='tight', 
           facecolor='white')

plt.show()