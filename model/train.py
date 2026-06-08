import dgl
import numpy as np
from tqdm import tqdm
from utils.loaddata import transform_graph


# def batch_level_train(model, graphs, train_loader, optimizer, max_epoch, device, n_dim=0, e_dim=0):
#     epoch_iter = tqdm(range(max_epoch))
#     for epoch in epoch_iter:
#         model.train()
#         loss_list = []
#         for _, batch in enumerate(train_loader):
#             batch_g = [transform_graph(graphs[idx][0], n_dim, e_dim).to(device) for idx in batch]
#             batch_g = dgl.batch(batch_g)
#             model.train()
#             loss = model(batch_g)

#             optimizer.zero_grad()
#             loss.backward()
#             optimizer.step()
#             loss_list.append(loss.item())
#             del batch_g
#         epoch_iter.set_description(f"Epoch {epoch} | train_loss: {np.mean(loss_list):.4f}")
#     return model

# 在model/train.py中修改batch_level_train函数
def batch_level_train(model, graphs, train_loader, optimizer, device, n_dim, e_dim, epoch):
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    for batch in train_loader:
        batch = batch.to(device)
        # 假设模型的前向传播返回损失
        loss = model(batch)
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1
    
    avg_loss = total_loss / num_batches
    print(f"Epoch {epoch+1}: Train Loss: {avg_loss:.4f}")
    return avg_loss