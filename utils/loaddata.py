import pickle as pkl
import time
import torch.nn.functional as F
import dgl
import networkx as nx
import json
from tqdm import tqdm
import os


class StreamspotDataset(dgl.data.DGLDataset):
    def process(self):
        pass

    def __init__(self, name):
        super(StreamspotDataset, self).__init__(name=name)
        if name == 'streamspot':
            path = './data/streamspot'
            num_graphs = 600
            self.graphs = []
            self.labels = []
            print('Loading {} dataset...'.format(name))
            for i in tqdm(range(num_graphs)):
                idx = i
                g = dgl.from_networkx(
                    nx.node_link_graph(json.load(open('{}/{}.json'.format(path, str(idx + 1))))),
                    node_attrs=['type'],
                    edge_attrs=['type']
                )
                self.graphs.append(g)
                if 300 <= idx <= 399:
                    self.labels.append(1)
                else:
                    self.labels.append(0)
        else:
            raise NotImplementedError

    def __getitem__(self, i):
        return self.graphs[i], self.labels[i]

    def __len__(self):
        return len(self.graphs)


class WgetDataset(dgl.data.DGLDataset):
    def process(self):
        pass

    def __init__(self, name):
        super(WgetDataset, self).__init__(name=name)
        if name == 'wget':
            path = './data/wget/'
            num_graphs = 150
            self.graphs = []
            self.labels = []
            print('Loading {} dataset...'.format(name))
            for i in tqdm(range(num_graphs)):
                idx = i
                g = dgl.from_networkx(
                    nx.node_link_graph(json.load(open('{}/{}.json'.format(path, str(idx))))),
                    node_attrs=['type'],
                    edge_attrs=['type']
                )
                self.graphs.append(g)
                if 0 <= idx <= 24:
                    self.labels.append(1)
                else:
                    self.labels.append(0)
        else:
            raise NotImplementedError

    def __getitem__(self, i):
        return self.graphs[i], self.labels[i]

    def __len__(self):
        return len(self.graphs)


def load_rawdata(name):
    if name == 'streamspot':
        path = './data/streamspot'
        if os.path.exists(path + '/graphs.pkl'):
            print('Loading processed {} dataset...'.format(name))
            raw_data = pkl.load(open(path + '/graphs.pkl', 'rb'))
        else:
            raw_data = StreamspotDataset(name)
            pkl.dump(raw_data, open(path + '/graphs.pkl', 'wb'))
    elif name == 'wget':
        path = './data/wget'
        if os.path.exists(path + '/graphs.pkl'):
            print('Loading processed {} dataset...'.format(name))
            raw_data = pkl.load(open(path + '/graphs.pkl', 'rb'))
        else:
            raw_data = WgetDataset(name)
            pkl.dump(raw_data, open(path + '/graphs.pkl', 'wb'))
    else:
        raise NotImplementedError
    return raw_data


def load_batch_level_dataset(dataset_name):
    dataset = load_rawdata(dataset_name)
    graph, _ = dataset[0]
    node_feature_dim = 0
    for g, _ in dataset:
        node_feature_dim = max(node_feature_dim, g.ndata["type"].max().item())
    edge_feature_dim = 0
    for g, _ in dataset:
        edge_feature_dim = max(edge_feature_dim, g.edata["type"].max().item())
    node_feature_dim += 1
    edge_feature_dim += 1
    full_dataset = [i for i in range(len(dataset))]
    train_dataset = [i for i in range(len(dataset)) if dataset[i][1] == 0]
    print('[n_graph, n_node_feat, n_edge_feat]: [{}, {}, {}]'.format(len(dataset), node_feature_dim, edge_feature_dim))

    return {'dataset': dataset,
            'train_index': train_dataset,
            'full_index': full_dataset,
            'n_feat': node_feature_dim,
            'e_feat': edge_feature_dim}


def transform_graph(g, node_feature_dim, edge_feature_dim):
    new_g = g.clone()
    new_g.ndata["attr"] = F.one_hot(g.ndata["type"].view(-1), num_classes=node_feature_dim).float()
    new_g.edata["attr"] = F.one_hot(g.edata["type"].view(-1), num_classes=edge_feature_dim).float()
    return new_g


def preload_entity_level_dataset(path):
    path = './data/' + path +'/graphs'
    if os.path.exists(path + '/metadata.json'):
        pass
    else:
        print('transforming')

        # 动态加载 train 和 test 文件
        train_gs = []
        i = 0
        while os.path.exists(path + f'/train{i}.pkl'):  # 动态加载 train 文件
            with open(path + f'/train{i}.pkl', 'rb') as f:
                graphs = pkl.load(f)
                train_gs.extend(graphs)
            i += 1

        test_gs = []
        i = 0
        while os.path.exists(path + f'/test{i}.pkl'):  # 动态加载 test 文件
            with open(path + f'/test{i}.pkl', 'rb') as f:
                graphs = pkl.load(f)
                test_gs.extend(graphs)
            i += 1

        # 加载 malicious.pkl 文件
        with open(path + '/malicious.pkl', 'rb') as f:
            malicious = pkl.load(f)

        # 计算节点和边的特征维度
        node_feature_dim = 0
        for g in train_gs:
            node_feature_dim = max(g.ndata["type"].max().item(), node_feature_dim)
        for g in test_gs:
            node_feature_dim = max(g.ndata["type"].max().item(), node_feature_dim)
        node_feature_dim += 1

        edge_feature_dim = 0
        for g in train_gs:
            edge_feature_dim = max(g.edata["type"].max().item(), edge_feature_dim)
        for g in test_gs:
            edge_feature_dim = max(g.edata["type"].max().item(), edge_feature_dim)
        edge_feature_dim += 1

        # 转换图数据
        result_test_gs = [transform_graph(g, node_feature_dim, edge_feature_dim) for g in test_gs]
        result_train_gs = [transform_graph(g, node_feature_dim, edge_feature_dim) for g in train_gs]

        # 保存 metadata 信息
        metadata = {
            'node_feature_dim': node_feature_dim,
            'edge_feature_dim': edge_feature_dim,
            'malicious': malicious,
            'n_train': len(result_train_gs),
            'n_test': len(result_test_gs)
        }

        # 保存 metadata.json 文件
        with open(path + '/metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f)

        # 保存训练集和测试集图
        for i, g in enumerate(result_train_gs):
            with open(path + f'/train{i}.pkl', 'wb') as f:
                pkl.dump(g, f)
        for i, g in enumerate(result_test_gs):
            with open(path + f'/test{i}.pkl', 'wb') as f:
                pkl.dump(g, f)


# def load_metadata(path):
#     preload_entity_level_dataset(path)
#     with open('./data/' + path + '/metadata.json', 'r', encoding='utf-8') as f:
#         metadata = json.load(f)
#     return metadata

def load_metadata(path):
    # 修正路径问题：你可以直接给出完整的路径
    graph_path = './data/trace/graphs/'  # 这里假设数据存放在 graphs 文件夹中

    # 检查是否存在这些文件
    for i in range(4):  # 假设你只有两个文件 train0.pkl 和 train1.pkl
        file_path = os.path.join(graph_path, f'train{i}.pkl')
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                data = pkl.load(f)
        else:
            print(f"File {file_path} not found!")
    
    # 加载 metadata.json 文件
    metadata_path = os.path.join('./data', path, 'graphs/metadata.json')
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    return metadata


def load_entity_level_dataset(path, t, n):
    preload_entity_level_dataset(path)
    with open('./data/' + path + '/graphs/{}{}.pkl'.format(t, n), 'rb') as f:
        data = pkl.load(f)
    return data
