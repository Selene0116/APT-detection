import argparse
import json
import os
import pickle as pkl
import shutil

import torch


def enhance_graph(g, edge_feature_dim,behavior_weight):
    new_g = g.clone()
    num_nodes = new_g.num_nodes()

    src, dst = new_g.edges()
    etype = new_g.edata["type"].long()

    device = new_g.ndata["attr"].device
    src = src.to(device)
    dst = dst.to(device)
    etype = etype.to(device)

    out_hist = torch.zeros(num_nodes, edge_feature_dim, device=device)
    in_hist = torch.zeros(num_nodes, edge_feature_dim, device=device)

    one_hot_edge = torch.nn.functional.one_hot(
        etype, num_classes=edge_feature_dim
    ).float()

    out_hist.index_add_(0, src, one_hot_edge)
    in_hist.index_add_(0, dst, one_hot_edge)

    # log 压缩，避免少数高频节点支配特征尺度。
    out_hist = torch.log1p(out_hist)
    in_hist = torch.log1p(in_hist)

    # 图内归一化到相近尺度，避免新增特征压过原始节点类型 one-hot。
    out_max = out_hist.max()
    in_max = in_hist.max()
    if out_max > 0:
        out_hist = out_hist / out_max
    if in_max > 0:
        in_hist = in_hist / in_max

    # new_g.ndata["attr"] = torch.cat(
    #     [new_g.ndata["attr"].float(), out_hist, in_hist],
    #     dim=1
    # )

    new_g.ndata["attr"] = torch.cat(
    [
        new_g.ndata["attr"].float(),
        behavior_weight * out_hist,
        behavior_weight * in_hist
    ],
    dim=1
)

    return new_g


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, choices=["cadets", "theia", "trace"])
    parser.add_argument("--suffix", default="bfeat")
    parser.add_argument("--behavior_weight", type=float, default=1.0)
    args = parser.parse_args()

    src_dir = f"data/{args.dataset}/graphs"
    dst_dataset = f"{args.dataset}_{args.suffix}"
    dst_dir = f"data/{dst_dataset}/graphs"

    os.makedirs(dst_dir, exist_ok=True)

    metadata_path = os.path.join(src_dir, "metadata.json")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(metadata_path)

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    edge_feature_dim = metadata["edge_feature_dim"]
    old_node_feature_dim = metadata["node_feature_dim"]
    new_node_feature_dim = old_node_feature_dim + 2 * edge_feature_dim

    print(f"source dataset: {args.dataset}")
    print(f"target dataset: {dst_dataset}")
    print(f"old node dim: {old_node_feature_dim}")
    print(f"edge dim: {edge_feature_dim}")
    print(f"new node dim: {new_node_feature_dim}")

    for name in sorted(os.listdir(src_dir)):
        src_path = os.path.join(src_dir, name)
        dst_path = os.path.join(dst_dir, name)

        if name.endswith(".pkl") and (name.startswith("train") or name.startswith("test")):
            print(f"enhancing {name} ...")
            with open(src_path, "rb") as f:
                g = pkl.load(f)
            #g = enhance_graph(g, edge_feature_dim)
            g = enhance_graph(g, edge_feature_dim, args.behavior_weight)
            with open(dst_path, "wb") as f:
                pkl.dump(g, f)
        elif name == "metadata.json":
            continue
        else:
            shutil.copy2(src_path, dst_path)

    metadata["node_feature_dim"] = new_node_feature_dim
    metadata["feature_enhancement"] = "node_type_onehot + outgoing_edge_type_hist + incoming_edge_type_hist"
    metadata["behavior_weight"] = args.behavior_weight
    metadata["source_dataset"] = args.dataset

    with open(os.path.join(dst_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("done")


if __name__ == "__main__":
    main()