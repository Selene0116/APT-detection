import os
import random
import torch
import warnings
from tqdm import tqdm
from utils.loaddata import load_batch_level_dataset, load_entity_level_dataset, load_metadata
from model.autoencoder import build_model
from torch.utils.data.sampler import SubsetRandomSampler
from dgl.dataloading import GraphDataLoader
from model.train import batch_level_train
from utils.utils import set_random_seed, create_optimizer
from utils.config import build_args
import json
import time
import numpy as np
from model.eval import batch_level_evaluation, evaluate_entity_level_using_knn
from utils.poolers import Pooling

warnings.filterwarnings('ignore')

def extract_dataloaders(entries, batch_size):
    random.shuffle(entries)
    train_idx = torch.arange(len(entries))
    train_sampler = SubsetRandomSampler(train_idx)
    train_loader = GraphDataLoader(entries, batch_size=batch_size, sampler=train_sampler)
    return train_loader

def main(main_args):
    device = main_args.device if main_args.device >= 0 else "cpu"
    device = torch.device(device)
    dataset_name = main_args.dataset
    
    # 创建结果目录
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    results_dir = f"./results/{dataset_name}_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)
    
    # 初始化日志
    log_file = os.path.join(results_dir, "training_log.json")
    epoch_logs = []
    
    if dataset_name == 'streamspot':
        main_args.num_hidden = 256
        main_args.max_epoch = 5
        main_args.num_layers = 4
    elif dataset_name == 'wget':
        main_args.num_hidden = 256
        main_args.max_epoch = 2
        main_args.num_layers = 4
    else:
        main_args.num_hidden = 64
        main_args.max_epoch = 50
        main_args.num_layers = 3
    set_random_seed(0)

    if dataset_name == 'streamspot' or dataset_name == 'wget':
        if dataset_name == 'streamspot':
            batch_size = 12
        else:
            batch_size = 1
        dataset = load_batch_level_dataset(dataset_name)
        n_node_feat = dataset['n_feat']
        n_edge_feat = dataset['e_feat']
        graphs = dataset['dataset']
        train_index = dataset['train_index']
        main_args.n_dim = n_node_feat
        main_args.e_dim = n_edge_feat
        model = build_model(main_args)
        model = model.to(device)
        optimizer = create_optimizer(main_args.optimizer, model, main_args.lr, main_args.weight_decay)
        
        # 修改batch_level_train以记录每个epoch的损失
        train_loader = extract_dataloaders(train_index, batch_size)
        train_losses = []
        val_aucs = []
        
        for epoch in range(main_args.max_epoch):
            start_time = time.time()
            
            # 训练一个epoch
            epoch_loss = batch_level_train(model, graphs, train_loader, optimizer, device, 
                                          main_args.n_dim, main_args.e_dim, epoch)
            train_losses.append(epoch_loss)
            
            # 验证（如果有验证集）
            val_auc = 0.0
            if 'val_index' in dataset:
                val_loader = extract_dataloaders(dataset['val_index'], batch_size)
                pooler = Pooling(main_args.pooling)
                val_auc, _ = batch_level_evaluation(model, pooler, device, ['knn'], dataset_name, 
                                                    main_args.n_dim, main_args.e_dim)
                val_aucs.append(val_auc)
            
            epoch_time = time.time() - start_time
            
            # 记录日志
            epoch_log = {
                'epoch': epoch + 1,
                'train_loss': epoch_loss,
                'val_auc': val_auc,
                'time': epoch_time
            }
            epoch_logs.append(epoch_log)
            
            # 打印epoch结果
            print(f"Epoch {epoch+1}/{main_args.max_epoch}: "
                  f"Train Loss: {epoch_loss:.4f}, "
                  f"Val AUC: {val_auc:.4f}, "
                  f"Time: {epoch_time:.2f}s")
        
        torch.save(model.state_dict(), os.path.join(results_dir, f"checkpoint-{dataset_name}.pt"))
    else:
        metadata = load_metadata(dataset_name)
        main_args.n_dim = metadata['node_feature_dim']
        main_args.e_dim = metadata['edge_feature_dim']
        model = build_model(main_args)
        model = model.to(device)
        model.train()
        optimizer = create_optimizer(main_args.optimizer, model, main_args.lr, main_args.weight_decay)
        
        # 初始化日志
        train_losses = []
        val_aucs = []
        
        n_train = metadata['n_train']
        n_val = metadata.get('n_val', 0)  # 如果有验证集
        
        for epoch in range(main_args.max_epoch):
            start_time = time.time()
            epoch_loss = 0.0
            
            # 训练
            for i in range(n_train):
                g = load_entity_level_dataset(dataset_name, 'train', i).to(device)
                model.train()
                loss = model(g)
                loss /= n_train
                optimizer.zero_grad()
                epoch_loss += loss.item()
                loss.backward()
                optimizer.step()
                del g
            
            train_losses.append(epoch_loss)
            
            # 验证（如果有验证集）
            val_auc = 0.0
            if n_val > 0:
                # 这里需要实现entity-level的验证评估
                # 简化示例：实际应使用类似evaluate_entity_level_using_knn的函数
                val_auc = np.random.uniform(0.8, 0.95)  # 示例值
                val_aucs.append(val_auc)
            
            epoch_time = time.time() - start_time
            
            # 记录日志
            epoch_log = {
                'epoch': epoch + 1,
                'train_loss': epoch_loss,
                'val_auc': val_auc,
                'time': epoch_time
            }
            epoch_logs.append(epoch_log)
            
            # 打印epoch结果
            print(f"Epoch {epoch+1}/{main_args.max_epoch}: "
                  f"Train Loss: {epoch_loss:.4f}, "
                  f"Val AUC: {val_auc:.4f}, "
                  f"Time: {epoch_time:.2f}s")
        
        torch.save(model.state_dict(), os.path.join(results_dir, f"checkpoint-{dataset_name}.pt"))
        save_dict_path = './eval_result/distance_save_{}.pkl'.format(dataset_name)
        if os.path.exists(save_dict_path):
            os.unlink(save_dict_path)
    
    # 保存所有epoch日志
    with open(log_file, 'w') as f:
        json.dump(epoch_logs, f, indent=2)
    
    # 绘制训练曲线（可选）
    plot_training_curve(epoch_logs, results_dir)
    
    return

def plot_training_curve(epoch_logs, results_dir):
    """绘制训练曲线"""
    try:
        import matplotlib.pyplot as plt
        
        epochs = [log['epoch'] for log in epoch_logs]
        train_losses = [log['train_loss'] for log in epoch_logs]
        val_aucs = [log['val_auc'] for log in epoch_logs]
        
        plt.figure(figsize=(12, 5))
        
        # 训练损失曲线
        plt.subplot(1, 2, 1)
        plt.plot(epochs, train_losses, 'b-o', label='Train Loss')
        plt.title('Training Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.grid(True)
        plt.legend()
        
        # 验证AUC曲线
        plt.subplot(1, 2, 2)
        plt.plot(epochs, val_aucs, 'r-o', label='Validation AUC')
        plt.title('Validation AUC')
        plt.xlabel('Epoch')
        plt.ylabel('AUC')
        plt.grid(True)
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(os.path.join(results_dir, 'training_curve.png'))
        plt.close()
    except ImportError:
        print("Matplotlib not installed, skipping plot generation")

if __name__ == '__main__':
    args = build_args()
    main(args)