
import re
import torch.nn as nn
import numpy as np
from IPython import display
from matplotlib import pyplot as plt
import time
import torch
import torchvision as tv
import torchvision.transforms as transforms
import torch.utils.data as data
import random
import os
import requests
import hashlib
import zipfile
import tarfile
import collections
import math
import torch.nn.functional as F
import torch as t
import pandas as pd


def use_svg_display():
    """使用svg格式在Jupyter中显示绘图"""
    display.set_matplotlib_formats('svg')


def set_figsize(figsize=(3.5, 2.5)):
    """设置matplotlib的图表大小"""
    use_svg_display()
    plt.rcParams['figure.figsize'] = figsize


def set_axes(axes, xlabel, ylabel, xlim, ylim, xscale, yscale, legend):
    """设置matplotlib的轴"""
    axes.set_xlabel(xlabel)
    axes.set_ylabel(ylabel)
    axes.set_xscale(xscale)
    axes.set_yscale(yscale)
    axes.set_xlim(xlim)
    axes.set_ylim(ylim)
    if legend:
        axes.legend(legend)
    axes.grid()


def plot(X, Y=None, xlabel=None, ylabel=None, legend=None, xlim=None,
         ylim=None, xscale='linear', yscale='linear',
         fmts=('-', 'm--', 'g-.', 'r:'), figsize=(3.5, 2.5), axes=None):
    """绘制数据点"""
    if legend is None:
        legend = []

    set_figsize(figsize)
    axes = axes if axes else plt.gca()

    # 如果X有一个轴，输出True
    def has_one_axis(X):
        return (hasattr(X, "ndim") and X.ndim == 1 or isinstance(X, list)
                and not hasattr(X[0], "__len__"))

    if has_one_axis(X):
        X = [X]
    if Y is None:
        X, Y = [[]] * len(X), X
    elif has_one_axis(Y):
        Y = [Y]
    if len(X) != len(Y):
        X = X * len(Y)
    axes.cla()
    for x, y, fmt in zip(X, Y, fmts):
        if len(x):
            axes.plot(x, y, fmt)
        else:
            axes.plot(y, fmt)
    set_axes(axes, xlabel, ylabel, xlim, ylim, xscale, yscale, legend)


class Timer:
    """记录多次运行时间"""

    def __init__(self):
        self.times = []
        self.start()

    def start(self):
        """启动计时器"""
        self.tik = time.time()

    def stop(self):
        """停止计时器并将时间记录在列表中"""
        self.times.append(time.time() - self.tik)
        return self.times[-1]

    def avg(self):
        """返回平均时间"""
        return sum(self.times) / len(self.times)

    def sum(self):
        """返回时间总和"""
        return sum(self.times)

    def cumsum(self):
        """返回累计时间"""
        return np.array(self.times).cumsum().tolist()


def get_fashion_mnist_labels(labels):  # @save
    """返回Fashion-MNIST数据集的文本标签"""
    text_labels = ['t-shirt', 'trouser', 'pullover', 'dress', 'coat',
                   'sandal', 'shirt', 'sneaker', 'bag', 'ankle boot']
    return [text_labels[int(i)] for i in labels]


def show_images(imgs, num_rows, num_cols, titles=None, scale=1.5):  # @save
    """绘制图像列表"""
    figsize = (num_cols * scale, num_rows * scale)
    _, axes = plt.subplots(num_rows, num_cols, figsize=figsize)
    axes = axes.flatten()
    for i, (ax, img) in enumerate(zip(axes, imgs)):
        if torch.is_tensor(img):
            # 图片张量
            ax.imshow(img.numpy())
        else:
            # PIL图片
            ax.imshow(img)
        ax.axes.get_xaxis().set_visible(False)
        ax.axes.get_yaxis().set_visible(False)
        if titles:
            ax.set_title(titles[i])
    return axes


def load_data_fashion_mnist(batch_size, resize=None, n_threads=0, data_root=r"./dataset"):
    """下载fashion-MNIST数据集 将其加载到内存当中去"""
    transform = [transforms.ToTensor()]
    if resize:
        transform.insert(0, transforms.Resize(size=resize))
    trans = transforms.Compose(transform)
    mnist_train = tv.datasets.FashionMNIST(
        root=data_root, train=True, transform=trans, download=True)
    mnist_test = tv.datasets.FashionMNIST(
        root=data_root, train=False, transform=trans, download=True)
    train_loader = data.DataLoader(
        mnist_train, batch_size, shuffle=True, num_workers=n_threads)
    test_loader = data.DataLoader(
        mnist_test, batch_size, shuffle=True, num_workers=n_threads)
    return train_loader, test_loader


def data_iter(batch_size: int, features: torch.Tensor, labels: torch.Tensor):
    num_examples = len(features)
    indices = list(range(num_examples))
    random.shuffle(indices)
    for i in range(0, num_examples, batch_size):
        batch_indices = torch.tensor(
            indices[i:min(i+batch_size, num_examples)])
        yield features[batch_indices], labels[batch_indices]


def annotate(text, xy, xytext):
    plt.gca().annotate(text, xy, xytext, arrowprops=dict(arrowstyle="->"))


def train_2d(trainer, steps=20, f_grad=None):  # @save
    """用定制的训练机优化2D目标函数"""
    # s1和s2是稍后将使用的内部状态变量
    x1, x2, s1, s2 = -5, -2, 0, 0
    results = [(x1, x2)]
    for i in range(steps):
        if f_grad:
            x1, x2, s1, s2 = trainer(x1, x2, s1, s2, f_grad)
        else:
            x1, x2, s1, s2 = trainer(x1, x2, s1, s2)
        results.append((x1, x2))
    print(f'epoch {i + 1}, x1: {float(x1):f}, x2: {float(x2):f}')
    return results


def show_trace_2d(f, results):  # @save
    """显示优化过程中2D变量的轨迹"""
    set_figsize()
    plt.plot(*zip(*results), '-o', color='#ff7f0e')
    x1, x2 = torch.meshgrid(torch.arange(-5.5, 1.0, 0.1),
                            torch.arange(-3.0, 1.0, 0.1), indexing="xy")
    plt.contour(x1, x2, f(x1, x2), colors='#1f77b4')
    plt.xlabel('x1')
    plt.ylabel('x2')


def download(name, cache_dir=os.path.join('..', 'dataset')):
    """下载一个DATA_HUB中的文件，返回本地文件名
    Defined in :numref:`sec_kaggle_house`"""
    assert name in DATA_HUB, f"{name} 不存在于 {DATA_HUB}"
    url, sha1_hash = DATA_HUB[name]
    os.makedirs(cache_dir, exist_ok=True)
    fname = os.path.join(cache_dir, url.split('/')[-1])
    if os.path.exists(fname):
        sha1 = hashlib.sha1()
        with open(fname, 'rb') as f:
            while True:
                data = f.read(1048576)
                if not data:
                    break
                sha1.update(data)
        if sha1.hexdigest() == sha1_hash:
            return fname  # 命中缓存
    print(f'正在从{url}下载{fname}...')
    r = requests.get(url, stream=True, verify=True)
    with open(fname, 'wb') as f:
        f.write(r.content)
    return fname


def download_extract(name, folder=None):
    """下载并解压zip/tar文件
    Defined in :numref:`sec_kaggle_house`"""
    fname = download(name)
    base_dir = os.path.dirname(fname)
    data_dir, ext = os.path.splitext(fname)
    if ext == '.zip':
        fp = zipfile.ZipFile(fname, 'r')
    elif ext in ('.tar', '.gz'):
        fp = tarfile.open(fname, 'r')
    else:
        assert False, '只有zip/tar文件可以被解压缩'
    fp.extractall(base_dir)
    return os.path.join(base_dir, folder) if folder else data_dir


def download_all():
    """下载DATA_HUB中的所有文件
    Defined in :numref:`sec_kaggle_house`"""
    for name in DATA_HUB:
        download(name)


def load_array(data_arrays, batch_size, is_train=True):
    """构造一个PyTorch数据迭代器
    Defined in :numref:`sec_linear_concise`"""
    dataset = data.TensorDataset(*data_arrays)
    return data.DataLoader(dataset, batch_size, shuffle=is_train)


def get_data_ch11(batch_size=10, n=1500):
    data = np.genfromtxt(download('airfoil'),
                         dtype=np.float32, delimiter='\t')
    data = torch.from_numpy((data - data.mean(axis=0)) / data.std(axis=0))
    data_iter = load_array((data[:n, :-1], data[:n, -1]),
                           batch_size, is_train=True)
    return data_iter, data.shape[1]-1


def linreg(X, w, b):
    """线性回归模型
    Defined in :numref:`sec_linear_scratch`"""
    return torch.matmul(X, w) + b


def squared_loss(y_hat, y):
    """均方损失
    Defined in :numref:`sec_linear_scratch`"""
    return (y_hat - torch.reshape(y, y_hat.shape)) ** 2 / 2


class Animator:
    """在动画中绘制数据"""

    def __init__(self, xlabel=None, ylabel=None, legend=None, xlim=None,
                 ylim=None, xscale='linear', yscale='linear',
                 fmts=('-', 'm--', 'g-.', 'r:'), nrows=1, ncols=1,
                 figsize=(3.5, 2.5)):
        """Defined in :numref:`sec_softmax_scratch`"""
        # 增量地绘制多条线
        if legend is None:
            legend = []
        use_svg_display()
        self.fig, self.axes = plt.subplots(nrows, ncols, figsize=figsize)
        if nrows * ncols == 1:
            self.axes = [self.axes, ]
        # 使用lambda函数捕获参数
        self.config_axes = lambda: set_axes(
            self.axes[0], xlabel, ylabel, xlim, ylim, xscale, yscale, legend)
        self.X, self.Y, self.fmts = None, None, fmts

    def add(self, x, y):
        # 向图表中添加多个数据点
        if not hasattr(y, "__len__"):
            y = [y]
        n = len(y)
        if not hasattr(x, "__len__"):
            x = [x] * n
        if not self.X:
            self.X = [[] for _ in range(n)]
        if not self.Y:
            self.Y = [[] for _ in range(n)]
        for i, (a, b) in enumerate(zip(x, y)):
            if a is not None and b is not None:
                self.X[i].append(a)
                self.Y[i].append(b)
        self.axes[0].cla()
        for x, y, fmt in zip(self.X, self.Y, self.fmts):
            self.axes[0].plot(x, y, fmt)
        self.config_axes()
        display.display(self.fig)
        display.clear_output(wait=True)


def evaluate_loss(net, data_iter, loss):
    """评估给定数据集上模型的损失
    Defined in :numref:`sec_model_selection`"""
    metric = Accumulator(2)  # 损失的总和,样本数量
    for X, y in data_iter:
        out = net(X)
        y = torch.reshape(y, out.shape)
        l = loss(out, y)
        metric.add(reduce_sum(l), size(l))
    return metric[0] / metric[1]


class Accumulator:
    """在n个变量上累加"""

    def __init__(self, n):
        """Defined in :numref:`sec_softmax_scratch`"""
        self.data = [0.0] * n

    def add(self, *args):
        self.data = [a + float(b) for a, b in zip(self.data, args)]

    def reset(self):
        self.data = [0.0] * len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]


def accuracy(y_hat, y):
    """计算预测正确的数量
    Defined in :numref:`sec_softmax_scratch`"""
    if len(y_hat.shape) > 1 and y_hat.shape[1] > 1:
        y_hat = argmax(y_hat, axis=1)
    cmp = astype(y_hat, y.dtype) == y
    return float(reduce_sum(astype(cmp, y.dtype)))


def try_gpu(i=0):
    """如果存在，则返回gpu(i)，否则返回cpu()
    Defined in :numref:`sec_use_gpu`"""
    if torch.cuda.device_count() >= i + 1:
        return torch.device(f'cuda:{i}')
    return torch.device('cpu')


def train_ch6(net, train_iter, test_iter, num_epochs, lr, device):
    """用GPU训练模型(在第六章定义)"""
    def init_weights(m):
        if type(m) == nn.Linear or type(m) == nn.Conv2d:
            nn.init.xavier_uniform_(m.weight)
    net.apply(init_weights)
    print('training on', device)
    net.to(device)
    optimizer = torch.optim.SGD(net.parameters(), lr=lr)
    loss = nn.CrossEntropyLoss()
    animator = Animator(xlabel='epoch', xlim=[1, num_epochs],
                        legend=['train loss', 'train acc', 'test acc'])
    timer, num_batches = Timer(), len(train_iter)
    for epoch in range(num_epochs):
        # 训练损失之和，训练准确率之和，样本数
        metric = Accumulator(3)
        net.train()
        for i, (X, y) in enumerate(train_iter):
            timer.start()
            optimizer.zero_grad()
            X, y = X.to(device), y.to(device)
            y_hat = net(X)
            l = loss(y_hat, y)
            l.backward()
            optimizer.step()
            with torch.no_grad():
                metric.add(l * X.shape[0], accuracy(y_hat, y), X.shape[0])
            timer.stop()
            train_l = metric[0] / metric[2]
            train_acc = metric[1] / metric[2]
            if (i + 1) % (num_batches // 5) == 0 or i == num_batches - 1:
                animator.add(epoch + (i + 1) / num_batches,
                             (train_l, train_acc, None))
        test_acc = evaluate_accuracy_gpu(net, test_iter)
        animator.add(epoch + 1, (None, None, test_acc))
    print(f'loss {train_l:.3f}, train acc {train_acc:.3f}, '
          f'test acc {test_acc:.3f}')
    print(f'{metric[2] * num_epochs / timer.sum():.1f} examples/sec '
          f'on {str(device)}')


def evaluate_accuracy_gpu(net, data_iter, device=None):  # @save
    """使用GPU计算模型在数据集上的精度"""
    if isinstance(net, nn.Module):
        net.eval()  # 设置为评估模式
        if not device:
            device = next(iter(net.parameters())).device
    # 正确预测的数量，总预测的数量
    metric = Accumulator(2)
    with torch.no_grad():
        for X, y in data_iter:
            if isinstance(X, list):
                # BERT微调所需的（之后将介绍）
                X = [x.to(device) for x in X]
            else:
                X = X.to(device)
            y = y.to(device)
            metric.add(accuracy(net(X), y), y.numel())
    return metric[0] / metric[1]


def count_corpus(tokens: list):
    # token 是1D列表或者是2D列表
    if len(tokens) == 0 or isinstance(tokens[0], list):
        tokens = [token for line in tokens for token in line]
    return collections.Counter(tokens)


class Vocab:
    """
    文本词表
    """

    def __init__(self, tokens=None, min_freq=0, reserved_tokens=None):
        if tokens is None:
            tokens = []
        if reserved_tokens is None:
            reserved_tokens = []
        # 按出现的频率排序
        counter = count_corpus(tokens)
        self._token_freqs = sorted(
            counter.items(), key=lambda x: x[1], reverse=True)

        # 未知词元的索引为0
        self.idx_to_token = ["<unk>"]+reserved_tokens
        self.token_to_idx = {token: idx for idx,
                             token in enumerate(self.idx_to_token)}

        for token, freq in self._token_freqs:
            if freq < min_freq:
                break
            if token not in self.token_to_idx:
                self.idx_to_token.append(token)
                self.token_to_idx[token] = len(self.idx_to_token)-1

    def __len__(self):
        return len(self.idx_to_token)

    def __getitem__(self, tokens):
        if not isinstance(tokens, (list, tuple)):
            return self.token_to_idx.get(tokens, self.unk)
        return [self.__getitem__(token) for token in tokens]

    def to_tokens(self, indices):
        if not isinstance(indices, (list, tuple)):
            return self.idx_to_token[indices]
        return [self.idx_to_token[index] for index in indices]

    @property
    def unk(self):
        return 0

    @property
    def token_freqs(self):
        return self._token_freqs


def read_time_machine():
    with open(download("time_machine"), "r") as f:
        lines = f.readlines()
    return [re.sub('[^A-Za-z]+', ' ', line).strip().lower() for line in lines]


def tokenize(lines, token="word"):
    if token == "word":
        return [line.split() for line in lines]
    elif token == "char":
        return [list(line) for line in lines]
    else:
        raise NotImplementedError("only support Word and Char")


def load_corpus_time_machine(max_tokens=-1):
    lines = read_time_machine()
    tokens = tokenize(lines, "char")
    vocab = Vocab(tokens)
    corpus = [vocab[token] for line in tokens for token in line]
    if max_tokens > 0:
        corpus = corpus[:max_tokens]
    return corpus, vocab


def seq_data_iter_random(corpus: list[str], batch_size: int, num_steps: int):
    # 从随机偏移量开始对序列进行分区，随机范围包括numsteps-1
    corpus = corpus[random.randint(0, num_steps-1):]
    # 减去一，因为要选取标签
    num_subseqs = (len(corpus)-1)//num_steps
    # 长度为num_steps的子序列的起始索引
    initial_indices = list(range(0, num_steps*num_subseqs, num_steps))
    # 在随机抽样的迭代过程中，来自两个相邻的、随机的、小批量的子序列不一定在原始序列上相邻
    random.shuffle(initial_indices)

    def data(pos: int):
        return corpus[pos:pos+num_steps]

    num_batches = num_subseqs//batch_size
    for i in range(0, batch_size*num_batches, batch_size):
        initial_indices_per_batch = initial_indices[i:i+batch_size]
        X = [data(j) for j in initial_indices_per_batch]
        Y = [data(j+1) for j in initial_indices_per_batch]
        yield torch.tensor(X), torch.tensor(Y)


def seq_data_iter_sequential(corpus, batch_size, num_steps):
    offset = random.randint(0, num_steps)

    num_tokens = ((len(corpus)-offset-1)//batch_size)*batch_size
    Xs = torch.tensor(corpus[offset:offset+num_tokens])
    Ys = torch.tensor(corpus[offset+1:offset+num_tokens+1])
    Xs, Ys = Xs.reshape(batch_size, -1), Ys.reshape(batch_size, -1)
    num_batches = Xs.shape[1]//num_steps
    for i in range(0, num_steps*num_batches, num_steps):
        X = Xs[:, i:i+num_steps]
        Y = Ys[:, i:i+num_steps]
        yield X, Y


class SeqDataLoader:
    def __init__(self, batch_size, num_steps, use_random_iter, max_tokens):
        if use_random_iter:
            self.data_iter_fn = seq_data_iter_random
        else:
            self.data_iter_fn = seq_data_iter_sequential
        self.corps, self.vocab = load_corpus_time_machine(max_tokens)
        self.batch_size, self.num_steps = batch_size, num_steps

    def __iter__(self):
        return self.data_iter_fn(self.corps, self.batch_size, self.num_steps)


def load_data_time_machine(batch_size, num_steps,  # @save
                           use_random_iter=False, max_tokens=10000):
    """返回时光机器数据集的迭代器和词表"""
    data_iter = SeqDataLoader(
        batch_size, num_steps, use_random_iter, max_tokens)
    return data_iter, data_iter.vocab


def sgd(params, lr, batch_size):
    """小批量随机梯度下降
    Defined in :numref:`sec_linear_scratch`"""
    with torch.no_grad():
        for param in params:
            param -= lr * param.grad / batch_size
            param.grad.zero_()


def predict_ch8(prefix, num_preds, net, vocab: Vocab, device: torch.device):
    state = net.begin_state(batch_size=1, device=device)
    outputs = [vocab[prefix[0]]]
    def get_input(): return torch.tensor(
        [outputs[-1]], device=device).reshape((1, 1))
    # 预热
    for y in prefix[1:]:
        _, state = net(get_input(), state)
        outputs.append(vocab[y])
    # 进行预测
    for _ in range(num_preds):
        y, state = net(get_input(), state)
        outputs.append(int(y.argmax(dim=1).reshape(1)))
    return "".join([vocab.idx_to_token[i] for i in outputs])


def train_epoch_ch8(net, train_iter, loss, updater, device, use_random_iter):
    state, timer = None, Timer()
    metric = Accumulator(2)
    for X, Y in train_iter:
        if state is None or use_random_iter:
            # 在第一次迭代或使用随机抽样时初始化state
            state = net.begin_state(batch_size=X.shape[0], device=device)
        else:
            if isinstance(net, nn.Module) and not isinstance(state, tuple):
                # state对于nn.GRU是个张量
                state.detach_()
            else:
                # state对于nn.LSTM或对于我们从零开始实现的模型是个张量
                for s in state:
                    s.detach_()
        y = Y.T.reshape(-1)
        X, y = X.to(device), y.to(device)
        y_hat, state = net(X, state)
        l = loss(y_hat, y.long()).mean()
        if isinstance(updater, torch.optim.Optimizer):
            updater.zero_grad()
            l.backward()
            grad_clipping(net, 1)
            updater.step()
        else:
            l.backward()
            grad_clipping(net, 1)
            # 因为已经调用了mean函数
            updater(batch_size=1)
        metric.add(l * y.numel(), y.numel())
    return math.exp(metric[0] / metric[1]), metric[1] / timer.stop()


def grad_clipping(net, theta):
    if isinstance(net, nn.Module):
        params = [p for p in net.parameters() if p.requires_grad]
    else:
        params = net.params
    norm = torch.sqrt(sum(torch.sum((p.grad**2)) for p in params))
    if norm > theta:
        for param in params:
            param.grad[:] *= theta/norm


def train_ch8(net, train_iter, vocab, lr, num_epochs, device, use_random_iter=False):
    loss = nn.CrossEntropyLoss()
    animator = Animator(xlabel='epoch', ylabel='perplexity',
                        legend=['train'], xlim=[10, num_epochs])

    # init
    if isinstance(net, nn.Module):
        updater = torch.optim.SGD(net.parameters(), lr)
    else:
        def updater(batch_size): return sgd(net.params, lr, batch_size)

    def predict(prefix): return predict_ch8(prefix, 50, net, vocab, device)
    # 训练和预测
    for epoch in range(num_epochs):
        ppl, speed = train_epoch_ch8(
            net, train_iter, loss, updater, device, use_random_iter)
        if (epoch+1) % 10 == 0:
            print(predict("time traveller"))
            animator.add(epoch+1, [ppl])
    print(f'困惑度 {ppl:.1f}, {speed:.1f} 词元/秒 {str(device)}')
    print(predict('time traveller'))
    print(predict('traveller'))


def show_heatmaps(matrices: torch.Tensor, xlabel, ylabel, titles=None, figsize=(2.5, 2.5), cmap="Reds"):
    """
    显示矩阵热图
    """
    use_svg_display()
    num_rows, num_cols = matrices.shape[0], matrices.shape[1]
    fig, axes = plt.subplots(
        num_rows, num_cols, figsize=figsize, sharex=True, sharey=True, squeeze=False)

    for i, (row_axes, row_matrices) in enumerate(zip(axes, matrices)):
        for j, (ax, matrix) in enumerate(zip(row_axes, row_matrices)):
            pcm = ax.imshow(matrix.detach.numpy(), cmap=cmap)
            if i == num_rows-1:
                ax.set_xlabel(xlabel)
            if j == 0:
                ax.set_ylabel(ylabel)
            if titles:
                ax.set_titile(titles[j])
    fig.colorbar(pcm, ax=axes, shrink=0.6)


class RNNModelScratch:
    def __init__(self, vocab_size, num_hiddens, device: torch.device, get_params, init_state, forward_fn):
        self.vocab_size = vocab_size
        self.num_hiddens = num_hiddens
        self.params = get_params(vocab_size, num_hiddens, device)
        self.init_state = init_state
        self.forward_fn = forward_fn

    def __call__(self, X: torch.Tensor, state: torch.Tensor):
        X = F.one_hot(X.T, self.vocab_size).type(torch.float32)
        return self.forward_fn(X, state, self.params)

    def begin_state(self, batch_size, device: torch.device):
        return self.init_state(batch_size, self.num_hiddens, device)


class RNNModel(nn.Module):
    """循环神经网络模型
    Defined in :numref:`sec_rnn-concise`"""

    def __init__(self, rnn_layer, vocab_size, **kwargs):
        super(RNNModel, self).__init__(**kwargs)
        self.rnn = rnn_layer
        self.vocab_size = vocab_size
        self.num_hiddens = self.rnn.hidden_size
        # 如果RNN是双向的（之后将介绍），num_directions应该是2，否则应该是1
        if not self.rnn.bidirectional:
            self.num_directions = 1
            self.linear = nn.Linear(self.num_hiddens, self.vocab_size)
        else:
            self.num_directions = 2
            self.linear = nn.Linear(self.num_hiddens * 2, self.vocab_size)

    def forward(self, inputs, state):
        X = F.one_hot(inputs.T.long(), self.vocab_size)
        X = X.to(torch.float32)
        Y, state = self.rnn(X, state)
        # 全连接层首先将Y的形状改为(时间步数*批量大小,隐藏单元数)
        # 它的输出形状是(时间步数*批量大小,词表大小)。
        output = self.linear(Y.reshape((-1, Y.shape[-1])))
        return output, state

    def begin_state(self, device, batch_size=1):
        if not isinstance(self.rnn, nn.LSTM):
            # nn.GRU以张量作为隐状态
            return torch.zeros((self.num_directions * self.rnn.num_layers,
                                batch_size, self.num_hiddens),
                               device=device)
        else:
            # nn.LSTM以元组作为隐状态
            return (torch.zeros((
                self.num_directions * self.rnn.num_layers,
                batch_size, self.num_hiddens), device=device),
                torch.zeros((
                    self.num_directions * self.rnn.num_layers,
                    batch_size, self.num_hiddens), device=device))


def truncate_pad(line, num_steps, padding_token):
    """
    截断或者填充文本序列
    """
    if len(line) > num_steps:
        return line[:num_steps]
    return line+[padding_token]*(num_steps-len(line))


def preprocess_nmt(text: str):
    """
    预处理英语-法语数据集
    """
    def no_space(char, prev_char):
        return char in set(',.!?') and prev_char != " "
    # 替换成普通空格，转小写
    text = text.replace("\u202f", " ").replace("\xa0", " ").lower()
    # 在单词和标点之间加入空格
    out = [" " + char if i >
           0 and no_space(char, text[i-1]) else char for i, char in enumerate(text)]
    return "".join(out)


def read_data_nmt():
    """载入“英语－法语”数据集"""
    data_dir = download_extract('fra-eng')
    with open(os.path.join(data_dir, 'fra.txt'), 'r',
              encoding='utf-8') as f:
        return f.read()


def tokenize_nmt(text: str, num_examples=None):
    """
    词元化英语-法语数据集
    """
    source, target = [], []
    for i, line in enumerate(text.split("\n")):
        if num_examples and i > num_examples:
            break
        # 以水平制表符分隔
        parts = line.split("\t")
        if len(parts) == 2:
            source.append(parts[0].split(" "))
            target.append(parts[1].split(" "))
    return source, target


def build_array_nmt(lines, vocab, num_steps):
    """
    将文本序列转换成小批量
    """
    lines = [vocab[l] for l in lines]
    lines = [l+[vocab["<eos>"]] for l in lines]
    array = torch.tensor(
        [truncate_pad(l, num_steps, vocab["<pad>"]) for l in lines])
    valid_len = (array != vocab["<pad>"]).type(torch.int32).sum(1)
    return array, valid_len


def load_data_nmt(batch_size, num_steps, num_examples=600):
    """返回翻译数据集的迭代器和词表"""
    text = preprocess_nmt(read_data_nmt())
    source, target = tokenize_nmt(text, num_examples)
    src_vocab = Vocab(source, min_freq=2,
                      reserved_tokens=['<pad>', '<bos>', '<eos>'])
    tgt_vocab = Vocab(target, min_freq=2,
                      reserved_tokens=['<pad>', '<bos>', '<eos>'])
    src_array, src_valid_len = build_array_nmt(source, src_vocab, num_steps)
    tgt_array, tgt_valid_len = build_array_nmt(target, tgt_vocab, num_steps)
    data_arrays = (src_array, src_valid_len, tgt_array, tgt_valid_len)
    data_iter = load_array(data_arrays, batch_size)
    return data_iter, src_vocab, tgt_vocab


def show_heatmaps(matrices: torch.Tensor, xlabel, ylabel, titles=None, figsize=(2.5, 2.5), cmap="Reds"):
    """
    显示矩阵热图
    """
    use_svg_display()
    num_rows, num_cols = matrices.shape[0], matrices.shape[1]
    fig, axes = plt.subplots(
        num_rows, num_cols, figsize=figsize, sharex=True, sharey=True, squeeze=False)

    for i, (row_axes, row_matrices) in enumerate(zip(axes, matrices)):
        for j, (ax, matrix) in enumerate(zip(row_axes, row_matrices)):
            pcm = ax.imshow(matrix.detach().numpy(), cmap=cmap)
            if i == num_rows-1:
                ax.set_xlabel(xlabel)
            if j == 0:
                ax.set_ylabel(ylabel)
            if titles:
                ax.set_titile(titles[j])
    fig.colorbar(pcm, ax=axes, shrink=0.6)


def sequence_mask(X: torch.Tensor, valid_len: torch.Tensor, value=0):
    """在序列中屏蔽不相关的项"""
    maxlen = X.size(1)
    mask = torch.arange((maxlen), dtype=torch.float32, device=X.device)[
        None, :] < valid_len[:, None]
    X[~mask] = value
    return X


def masked_softmax(X: torch.Tensor, valid_lens: torch.Tensor):

    if valid_lens is None:
        return F.softmax(X, dim=-1)
    else:
        shape = X.shape
        if valid_lens.dim() == 1:
            valid_lens = torch.repeat_interleave(valid_lens, shape[1])
        else:
            valid_lens = valid_lens.reshape(-1)
        # 最后一个轴上被这比的元素使用一个非常大的肤质来替换，是softmax输出为0
        X = sequence_mask(X.reshape(-1, shape[-1]), valid_lens, value=-1e6)
        return F.softmax(X.reshape(shape), dim=-1)


class Encoder(nn.Module):
    def __init__(self, **kwargs):
        super(Encoder, self).__init__(**kwargs)

    def forward(self, X: torch.Tensor, *args):
        raise NotImplementedError


class Decoder(nn.Module):
    def __init__(self, **kwargs):
        super(Decoder, self).__init__(**kwargs)

    def init_state(self, enc_outputs, *args):
        raise NotImplementedError

    def forward(self, X: torch.Tensor, state):
        raise NotImplementedError


class EncoderDecoder(nn.Module):
    def __init__(self, encoder: Encoder, decoder: Decoder, **kwargs):
        super().__init__(**kwargs)
        self.encoder = encoder
        self.decoder = decoder

    def forward(self, enc_X: torch.Tensor, dec_X: torch.Tensor, *args) -> tuple[torch.Tensor, torch.Tensor]:
        """
        前向传播函数
        """
        enc_outputs = self.encoder(enc_X, *args)
        dec_state = self.decoder.init_state(enc_outputs, *args)
        return self.decoder.forward(dec_X, dec_state)


# 加性注意力
class AdditiveAttention(nn.Module):
    def __init__(self, key_size, query_size, num_hiddens, dropout, **kwargs):
        super().__init__(**kwargs)
        self.W_k = nn.Linear(key_size, num_hiddens, bias=False)
        self.W_q = nn.Linear(query_size, num_hiddens, bias=False)
        self.w_v = nn.Linear(num_hiddens, 1, bias=False)
        self.dropout = nn.Dropout(dropout)

    def forward(self, queries, keys, values, valid_lens):
        queries, keys = self.W_q.forward(queries), self.W_k.forward(keys)
        # 维度扩展之后，
        # queries.shape = batch_size, num_queries, 1, num_hidden
        # key.shape = batch_size, 1, num_kvs , num_hiddens
        # 使用广播形式进行求和
        features = queries.unsqueeze(2) + keys.unsqueeze(1)
        features = torch.tanh(features)
        # self.w_v只有一个输出，因此从形状中移除最后的那个维度
        # socres.shape = batch_size, num_queries, num_kvs
        scores = self.w_v.forward(features).squeeze(-1)
        self.attention_weights = masked_softmax(scores, valid_lens)
        return torch.bmm(self.dropout(self.attention_weights), values)


class DotProductAttention(nn.Module):
    def __init__(self, dropout, **kwargs):
        super().__init__(**kwargs)
        self.dropout = nn.Dropout(dropout)

    def forward(self, queries, keys, values, valid_lens=None):
        d = queries.shape[-1]
        scores = torch.bmm(queries, keys.transpose(1, 2))/math.sqrt(d)
        self.attention_weights = masked_softmax(scores, valid_lens)
        return torch.bmm(self.dropout(self.attention_weights), values)


class Seq2SeqEncoder(Encoder):
    def __init__(self, vocab_size, embed_size, num_hiddens, num_layers, dropout=0, **kwargs):
        super().__init__(**kwargs)
        # 定义嵌入层
        self.embedding = nn.Embedding(vocab_size, embed_size)
        self.rnn = nn.GRU(embed_size, num_hiddens, num_layers, dropout=dropout)

    def forward(self, X: torch.Tensor, *args):
        # X.shape = [batch_size,num_steps,emb_size]
        X = self.embedding.forward(X)
        # 第一个轴对应时间步 , equals = Tensor.transpose(1,0,2)
        X = X.permute(1, 0, 2)
        # 如果没有提及状态，默认为0
        output, state = self.rnn.forward(X)
        # output.shape = [num_steps,batch_size,num_hiddens]
        # 在这里 output还要经过线性层才能够输出想要的维度
        # state[0].shape =[num_layers,batch_size,num_hiddens]
        return output, state


def train_seq2seq(net: nn.Module, data_iter, lr, num_epochs, tgt_vocab, device: t.device):

    def xavier_init_weights(m: nn.Module):
        if type(m) == nn.Linear:
            nn.init.xavier_uniform_(m.weight)
        if type(m) == nn.GRU:
            for param in m._flat_weights_names:
                if "weight" in param:
                    nn.init.xavier_uniform_(m._parameters[param])

    net.apply(xavier_init_weights)
    net.to(device)
    optimizer = t.optim.Adam(net.parameters(), lr=lr)
    loss = MaskedSoftmaxCELoss()
    net.train()
    animator = Animator(xlabel="epoch", ylabel="loss", xlim=[10, num_epochs])

    for epoch in range(num_epochs):
        timer = Timer()
        metric = Accumulator(2)

        for batch in data_iter:
            optimizer.zero_grad()
            # to device
            X, X_valid_len, Y, Y_valid_len = [x.to(device) for x in batch]
            # 获取开始符的下标
            bos = t.tensor([tgt_vocab["<bos>"]]*Y.shape[0],
                           device=device).reshape(-1, 1)
            # 在每个句子之前加上开始符
            dec_input = t.cat([bos, Y[:, :-1]], 1)
            Y_hat, _ = net.forward(X, dec_input, X_valid_len)
            l = loss.forward(Y_hat, Y, Y_valid_len)
            l.sum().backward()
            grad_clipping(net, 1)
            num_tokens = Y_valid_len.sum()
            optimizer.step()
            with t.no_grad():
                metric.add(l.sum(), num_tokens)
        if (epoch+1) % 10 == 0:
            animator.add(epoch+1, (metric[0]/metric[1],))
    print(f'loss {metric[0] / metric[1]:.3f}, {metric[1] / timer.stop():.1f} '
          f'tokens/sec on {str(device)}')


def sequence_mask(X: t.Tensor, valid_len: t.Tensor, value=0):
    """在序列中屏蔽不相关的项"""
    maxlen = X.size(1)
    mask = t.arange((maxlen), dtype=t.float32, device=X.device)[
        None, :] < valid_len[:, None]
    X[~mask] = value
    return X


class MaskedSoftmaxCELoss(nn.CrossEntropyLoss):
    def forward(self, pred: t.Tensor, label: t.Tensor, valid_len: t.Tensor):
        # pred.shape = batch,step,vsize
        # label.shape =batch,step
        # valid_len.shape = batch,
        weights = t.ones_like(label)
        weights = sequence_mask(weights, valid_len)
        self.reduction = "none"
        pred = pred.permute(0, 2, 1)
        unweighted_loss = super().forward(pred, label)
        weighted_loss = (unweighted_loss*weights).mean(dim=1)
        return weighted_loss


def predict_seq2seq(net, src_sentence, src_vocab, tgt_vocab, num_steps,
                    device, save_attention_weights=False):
    """序列到序列模型的预测
    Defined in :numref:`sec_seq2seq_training`"""
    # 在预测时将net设置为评估模式
    net.eval()
    src_tokens = src_vocab[src_sentence.lower().split(' ')] + [
        src_vocab['<eos>']]
    enc_valid_len = torch.tensor([len(src_tokens)], device=device)
    src_tokens = truncate_pad(src_tokens, num_steps, src_vocab['<pad>'])
    # 添加批量轴
    enc_X = torch.unsqueeze(
        torch.tensor(src_tokens, dtype=torch.long, device=device), dim=0)
    enc_outputs = net.encoder(enc_X, enc_valid_len)
    dec_state = net.decoder.init_state(enc_outputs, enc_valid_len)
    # 添加批量轴
    dec_X = torch.unsqueeze(torch.tensor(
        [tgt_vocab['<bos>']], dtype=torch.long, device=device), dim=0)
    output_seq, attention_weight_seq = [], []
    for _ in range(num_steps):
        Y, dec_state = net.decoder(dec_X, dec_state)
        # 我们使用具有预测最高可能性的词元，作为解码器在下一时间步的输入
        dec_X = Y.argmax(dim=2)
        pred = dec_X.squeeze(dim=0).type(torch.int32).item()
        # 保存注意力权重（稍后讨论）
        if save_attention_weights:
            attention_weight_seq.append(net.decoder.attention_weights)
        # 一旦序列结束词元被预测，输出序列的生成就完成了
        if pred == tgt_vocab['<eos>']:
            break
        output_seq.append(pred)
    return ' '.join(tgt_vocab.to_tokens(output_seq)), attention_weight_seq


def bleu(pred_seq, label_seq, k):  # @save
    """计算BLEU"""
    pred_tokens, label_tokens = pred_seq.split(' '), label_seq.split(' ')
    len_pred, len_label = len(pred_tokens), len(label_tokens)
    score = math.exp(min(0, 1 - len_label / len_pred))
    for n in range(1, k + 1):
        num_matches, label_subs = 0, collections.defaultdict(int)
        for i in range(len_label - n + 1):
            label_subs[' '.join(label_tokens[i: i + n])] += 1
        for i in range(len_pred - n + 1):
            if label_subs[' '.join(pred_tokens[i: i + n])] > 0:
                num_matches += 1
                label_subs[' '.join(pred_tokens[i: i + n])] -= 1
        score *= math.pow(num_matches / (len_pred - n + 1), math.pow(0.5, n))
    return score


def transpose_qkv(X: torch.Tensor, num_heads: int):
    """
    为了多注意力的并行计算而转换形状
    """
    # 输入X的形状:(batch_size，查询或者“键－值”对的个数，num_hiddens)
    # 输出X的形状:(batch_size，查询或者“键－值”对的个数，num_heads，num_hiddens/num_heads)
    X = X.reshape(X.shape[0], X.shape[1], num_heads, -1)
    # 输出X的形状:(batch_size，num_heads，查询或者“键－值”对的个数,
    # num_hiddens/num_heads)
    X = X.permute(0, 2, 1, 3)
    # 最终输出 (batch_size*num_heads,查询或者“键－值”对的个数,num_hiddens/num_heads)
    return X.reshape(-1, X.shape[2], X.shape[3])


def transpose_output(X: torch.Tensor, num_heads):
    """逆转transpose_qkv函数的操作"""
    X = X.reshape(-1, num_heads, X.shape[1], X.shape[2])
    X = X.permute(0, 2, 1, 3)
    return X.reshape(X.shape[0], X.shape[1], -1)


class MultiHeadAttention(nn.Module):
    def __init__(self, key_size, query_size, value_size, num_hiddens, num_heads, dropout, bias=False, **kwargs):
        super().__init__(**kwargs)
        self.num_heads = num_heads
        self.attention = DotProductAttention(dropout)
        self.W_q = nn.Linear(query_size, num_hiddens, bias=bias)
        self.W_k = nn.Linear(key_size, num_hiddens, bias=bias)
        self.W_v = nn.Linear(value_size, num_hiddens, bias=bias)
        self.W_o = nn.Linear(num_hiddens, num_hiddens, bias=bias)

    def forward(self, queries, keys, values, valid_lens):
        # 将这些玩意拆成batch实现并行化
        # queries, keys, values.shape = (batch_size, num_of_q/k/v s,num_hiddens)
        # valied_lens.shape = (batch_size,num_queries)
        queries = transpose_qkv(self.W_q.forward(queries), self.num_heads)
        keys = transpose_qkv(self.W_k.forward(keys), self.num_heads)
        values = transpose_qkv(self.W_v.forward(values), self.num_heads)

        if valid_lens is not None:
            valid_lens = t.repeat_interleave(
                valid_lens, repeats=self.num_heads, dim=0)
        output = self.attention(queries, keys, values, valid_lens)

        # output_concat的形状:(batch_size，查询的个数，num_hiddens)
        output_concat = transpose_output(output, self.num_heads)
        return self.W_o(output_concat)


class PositionalEncoding(nn.Module):
    def __init__(self, num_hiddens, dropout, max_len=1000):
        super().__init__()
        self.dropout = nn.Dropout(dropout)
        # 创建一个足够长的P
        self.p = t.zeros((1, max_len, num_hiddens))
        X = t.arange(max_len, dtype=t.float32).reshape(-1, 1)/t.pow(10000,
                                                                    t.arange(0, num_hiddens, 2, dtype=t.float32)/num_hiddens)
        self.p[:, :, 0::2] = t.sin(X)
        self.p[:, :, 1::2] = t.cos(X)

    def forward(self, X):
        X = X+self.p[:, :X.shape[1], :].to(X.device)
        return self.dropout.forward(X)


class AttentionDecoder(Decoder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def attention_weights(self):
        raise NotImplementedError
# @save


def train_batch_ch13(net, X, y, loss, trainer, devices):
    """用多GPU进行小批量训练"""
    if isinstance(X, list):
        # 微调BERT中所需（稍后讨论）
        X = [x.to(devices[0]) for x in X]
    else:
        X = X.to(devices[0])
    y = y.to(devices[0])
    net.train()
    trainer.zero_grad()
    pred = net(X)
    l = loss(pred, y)
    l.sum().backward()
    trainer.step()
    train_loss_sum = l.sum()
    train_acc_sum = accuracy(pred, y)
    return train_loss_sum, train_acc_sum

# @save


def train_ch13(net, train_iter, test_iter, loss, trainer, num_epochs,
               devices=[t.device("cuda:0")]):
    """用多GPU进行模型训练"""
    timer, num_batches = Timer(), len(train_iter)
    animator = Animator(xlabel='epoch', xlim=[1, num_epochs], ylim=[0, 1],
                        legend=['train loss', 'train acc', 'test acc'])
    net = nn.DataParallel(net, device_ids=devices).to(devices[0])
    for epoch in range(num_epochs):
        # 4个维度：储存训练损失，训练准确度，实例数，特点数
        metric = Accumulator(4)
        for i, (features, labels) in enumerate(train_iter):
            timer.start()
            l, acc = train_batch_ch13(
                net, features, labels, loss, trainer, devices)
            metric.add(l, acc, labels.shape[0], labels.numel())
            timer.stop()
            if (i + 1) % (num_batches // 5) == 0 or i == num_batches - 1:
                animator.add(epoch + (i + 1) / num_batches,
                             (metric[0] / metric[2], metric[1] / metric[3],
                              None))
        test_acc = evaluate_accuracy_gpu(net, test_iter)
        animator.add(epoch + 1, (None, None, test_acc))
    print(f'loss {metric[0] / metric[2]:.3f}, train acc '
          f'{metric[1] / metric[3]:.3f}, test acc {test_acc:.3f}')
    print(f'{metric[2] * num_epochs / timer.sum():.1f} examples/sec on '
          f'{str(devices)}')


def box_corner_to_center(boxes: t.Tensor):
    """从（左上，右下）转换到（中间，宽度，高度）"""
    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    cx = (x1+x2)/2
    cy = (y1+y2)/2
    w = x2-x1
    h = y2-y1
    boxes = t.stack((cx, cy, w, h), dim=-1)
    return boxes


def box_center_to_corner(boxes: t.Tensor):
    """从（中间，宽度，高度）转换到（左上，右下）"""
    cx, cy, w, h = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    x1 = cx - 0.5*w
    y1 = cy-0.5*h
    x2 = cx+0.5*w
    y2 = cy+0.5*h
    boxes = t.stack((x1, y1, x2, y2), dim=-1)
    return boxes


def bbox_to_rect(bbox, color):
    # 将边界框(左上x,左上y,右下x,右下y)格式转换成matplotlib格式：
    # ((左上x,左上y),宽,高)
    return plt.Rectangle(
        xy=(bbox[0], bbox[1]), width=bbox[2]-bbox[0], height=bbox[3]-bbox[1],
        fill=False, edgecolor=color, linewidth=2
    )


def multibox_prior(data: t.Tensor, sizes, ratios):
    """
    以每个像素点为中心，总共生成len(sizes)+len(ratios)-1 * w * h个锚框
    生成的锚框数组的shape为[1,h*w,len(sizes)+len(ratios)-1]
    """
    in_height, in_width = data.shape[-2:]
    device, num_sizes, num_ratios = data.device, len(sizes), len(ratios)
    boxes_per_pixel = (num_sizes+num_ratios-1)
    size_tensor = t.tensor(sizes, device=device)
    ratio_tensor = t.tensor(ratios, device=device)

    # 为了将锚点移到像素的中心，需要设置偏移量
    # 因为一个像素的高为1，宽为1，所以选择偏移到中心0.5,0.5
    offset_h, offset_w = 0.5, 0.5
    steps_h = 1.0/in_height
    steps_w = 1.0 / in_width
    # 生成锚框的所有中心点
    center_h = (t.arange(in_height, device=device)+offset_h) * steps_h
    center_w = (t.arange(in_width, device=device)+offset_w)*steps_w
    shift_y, shift_x = t.meshgrid(center_h, center_w, indexing="ij")
    shift_y, shift_x = shift_y.reshape(-1), shift_x.reshape(-1)

    # 生成boxes_per_pixel个高和宽
    # 之后用于创建锚框的四个坐标(xmin,xmax,ymin,ymax)
    # 在下一行中，我们要*in_height/in_width是为了对锚框的坐标进行一个归一化，不然就不能生成正方形的锚框啦
    w = t.cat((size_tensor*t.sqrt(ratio_tensor[0]), sizes[0]
              * t.sqrt(ratio_tensor[1:])))*in_height/in_width
    h = t.cat(
        (size_tensor/t.sqrt(ratio_tensor[0]), sizes[0]/t.sqrt(ratio_tensor[1:])))
    # 除以2来获得半高和半宽
    anchor_manipulations = t.stack(
        (-w, -h, w, h)).T.repeat(in_height*in_width, 1)/2
    # 每个中心点都有boxes_per_pixel个锚框
    # 所以要重复这么多次
    out_grid = t.stack([shift_x, shift_y, shift_x, shift_y],
                       dim=1,).repeat_interleave(boxes_per_pixel, dim=0)
    output = out_grid + anchor_manipulations
    return output.unsqueeze(0)


def show_bboxes(axes, bboxes, labels=None, colors=None):
    """
    显示所有的边界框
    """
    def _make_list(obj, defalut_values=None):
        """
        如果存在单个元素的话，就将它转换成列表，方便统一处理
        """
        if obj is None:
            obj = defalut_values
        elif not isinstance(obj, (list, tuple)):
            obj = [obj]
        return obj

    labels = _make_list(labels)
    colors = _make_list(colors, ['b', 'g', 'r', 'm', 'c'])

    for i, bbox in enumerate(bboxes):
        color = colors[i % len(colors)]
        rect = bbox_to_rect(bbox.detach().numpy(), color)
        axes.add_patch(rect)
        if labels and len(labels) > i:
            text_color = "k" if color == "w" else "w"
            axes.text(rect.xy[0], rect.xy[1], labels[i], va="center", ha="center",
                      fontsize="9", color=text_color, bbox=dict(facecolor=color, lw=0))


def box_iou(boxes1, boxes2):
    """
    计算两个锚框或者边界框列表中成对的交并比(并行)
    返回的是(box1数量，box2数量)shape的Jaccard值
    """
    def box_area(boxes): return (
        (boxes[:, 2] - boxes[:, 0])*(boxes[:, 3] - boxes[:, 1]))
    # boxes1,boxes2,areas1,areas2的形状:
    # boxes1：(boxes1的数量,4),
    # boxes2：(boxes2的数量,4),
    # areas1：(boxes1的数量,),
    # areas2：(boxes2的数量,)
    areas1 = box_area(boxes1)
    areas2 = box_area(boxes2)
    # inter_upperlefts,inter_lowerrights,inters的形状:
    # (boxes1的数量,boxes2的数量,2)
    inter_upperlefts = t.max(boxes1[:, None, :2], boxes2[:, :2])
    inter_lowerrights = torch.min(boxes1[:, None, 2:], boxes2[:, 2:])
    inters = (inter_lowerrights-inter_upperlefts).clamp(min=0)
    # inter_areas and union_areas的形状:(boxes1的数量,boxes2的数量)
    inter_areas = inters[:, :, 0]*inters[:, :, 1]
    union_areas = areas1[:, None]+areas2-inter_areas
    return inter_areas/union_areas


def assign_anchor_to_bbox(ground_truth, anchors, device, iou_threshold=0.5):
    """将最接近的真实边界框分配给锚框"""
    num_anchors, num_gt_boxes = anchors.shape[0], ground_truth.shape[0]
    # 位于第i行和第j列的元素x_ij是锚框i和真实边界框j的IoU
    jaccard = box_iou(anchors, ground_truth)
    # 对于每个锚框，分配的真实边界框的张量
    anchors_bbox_map = torch.full((num_anchors,), -1, dtype=torch.long,
                                  device=device)
    # 根据阈值，决定是否分配真实边界框
    max_ious, indices = torch.max(jaccard, dim=1)
    anc_i = torch.nonzero(max_ious >= 0.5).reshape(-1)
    box_j = indices[max_ious >= 0.5]
    anchors_bbox_map[anc_i] = box_j
    col_discard = torch.full((num_anchors,), -1)
    row_discard = torch.full((num_gt_boxes,), -1)
    for _ in range(num_gt_boxes):
        max_idx = torch.argmax(jaccard)
        box_idx = (max_idx % num_gt_boxes).long()
        anc_idx = (max_idx / num_gt_boxes).long()
        anchors_bbox_map[anc_idx] = box_idx
        jaccard[:, box_idx] = col_discard
        jaccard[anc_idx, :] = row_discard
    return anchors_bbox_map


def offset_boxes(anchors, assigned_bb, eps=1e-6):
    """对锚框偏移量的转换"""
    c_anc = box_corner_to_center(anchors)
    c_assigned_bb = box_corner_to_center(assigned_bb)
    offset_xy = 10 * (c_assigned_bb[:, :2] - c_anc[:, :2]) / c_anc[:, 2:]
    offset_wh = 5 * torch.log(eps + c_assigned_bb[:, 2:] / c_anc[:, 2:])
    offset = torch.cat([offset_xy, offset_wh], axis=1)
    return offset


def multibox_target(anchors, labels):
    """使用真实边界框标记锚框"""
    batch_size, anchors = labels.shape[0], anchors.squeeze(0)
    batch_offset, batch_mask, batch_class_labels = [], [], []
    device, num_anchors = anchors.device, anchors.shape[0]
    for i in range(batch_size):
        label = labels[i, :, :]
        anchors_bbox_map = assign_anchor_to_bbox(
            label[:, 1:], anchors, device)
        bbox_mask = ((anchors_bbox_map >= 0).float().unsqueeze(-1)).repeat(
            1, 4)
        # 将类标签和分配的边界框坐标初始化为零
        class_labels = torch.zeros(num_anchors, dtype=torch.long,
                                   device=device)
        assigned_bb = torch.zeros((num_anchors, 4), dtype=torch.float32,
                                  device=device)
        # 使用真实边界框来标记锚框的类别。
        # 如果一个锚框没有被分配，我们标记其为背景（值为零）
        indices_true = torch.nonzero(anchors_bbox_map >= 0)
        bb_idx = anchors_bbox_map[indices_true]
        class_labels[indices_true] = label[bb_idx, 0].long() + 1
        assigned_bb[indices_true] = label[bb_idx, 1:]
        # 偏移量转换
        offset = offset_boxes(anchors, assigned_bb) * bbox_mask
        batch_offset.append(offset.reshape(-1))
        batch_mask.append(bbox_mask.reshape(-1))
        batch_class_labels.append(class_labels)
    bbox_offset = torch.stack(batch_offset)
    bbox_mask = torch.stack(batch_mask)
    class_labels = torch.stack(batch_class_labels)
    return (bbox_offset, bbox_mask, class_labels)


def offset_inverse(anchors, offset_preds):
    """根据带有预测偏移量的锚框来预测边界框，\n
    该函数以锚框和偏移量预测作为输入，并应用逆偏移变换来返回预测的边界框坐标"""
    anc = box_corner_to_center(anchors)
    pred_bbox_xy = (offset_preds[:, :2] * anc[:, 2:] / 10) + anc[:, :2]
    pred_bbox_wh = torch.exp(offset_preds[:, 2:] / 5) * anc[:, 2:]
    pred_bbox = torch.cat((pred_bbox_xy, pred_bbox_wh), axis=1)
    predicted_bbox = box_center_to_corner(pred_bbox)
    return predicted_bbox


def nms(boxes, scores, iou_threshold):
    """对预测边界框的置信度进行排序"""
    B = torch.argsort(scores, dim=-1, descending=True)
    keep = []  # 保留预测边界框的指标
    while B.numel() > 0:
        i = B[0]
        keep.append(i)
        if B.numel() == 1:
            break
        iou = box_iou(boxes[i, :].reshape(-1, 4),
                      boxes[B[1:], :].reshape(-1, 4)).reshape(-1)
        inds = torch.nonzero(iou <= iou_threshold).reshape(-1)
        B = B[inds + 1]
    return torch.tensor(keep, device=boxes.device)


def multibox_detection(cls_probs, offset_preds, anchors, nms_threshold=0.5,
                       pos_threshold=0.009999999):
    """使用非极大值抑制来预测边界框"""
    device, batch_size = cls_probs.device, cls_probs.shape[0]
    anchors = anchors.squeeze(0)
    num_classes, num_anchors = cls_probs.shape[1], cls_probs.shape[2]
    out = []
    for i in range(batch_size):
        cls_prob, offset_pred = cls_probs[i], offset_preds[i].reshape(-1, 4)
        conf, class_id = torch.max(cls_prob[1:], 0)
        predicted_bb = offset_inverse(anchors, offset_pred)
        keep = nms(predicted_bb, conf, nms_threshold)

        # 找到所有的non_keep索引，并将类设置为背景
        all_idx = torch.arange(num_anchors, dtype=torch.long, device=device)
        combined = torch.cat((keep, all_idx))
        uniques, counts = combined.unique(return_counts=True)
        non_keep = uniques[counts == 1]
        all_id_sorted = torch.cat((keep, non_keep))
        class_id[non_keep] = -1
        class_id = class_id[all_id_sorted]
        conf, predicted_bb = conf[all_id_sorted], predicted_bb[all_id_sorted]
        # pos_threshold是一个用于非背景预测的阈值
        below_min_idx = (conf < pos_threshold)
        class_id[below_min_idx] = -1
        conf[below_min_idx] = 1 - conf[below_min_idx]
        pred_info = torch.cat((class_id.unsqueeze(1),
                               conf.unsqueeze(1),
                               predicted_bb), dim=1)
        out.append(pred_info)
    return torch.stack(out)


def read_data_bananas(is_train=True):
    """
    读取香蕉检测数据集中的图片和标签
    """
    data_dir = download_extract("banana-detection")
    csv_fname = os.path.join(
        data_dir, "bananas_train" if is_train else "bananas_val", "label.csv")
    csv_data = pd.read_csv(csv_fname)
    csv_data = csv_data.set_index("img_name")
    images, targets = [], []
    for img_name, target in csv_data.iterrows():
        images.append(tv.io.read_image(os.path.join(
            data_dir, "bananas_train" if is_train else "bananas_val", "images", f"{img_name}")))
        # target 包含 (class,x1,y1,x2,y2)
        targets.append(list(target))
    return images, t.tensor(targets).unsqueeze(1)/256


class BananasDataset(data.Dataset):
    """
    一个用于加载香蕉检测数据集的自定义数据集
    """

    def __init__(self, is_train):
        self.features, self.labels = read_data_bananas(is_train)
        print("read" + str(len(self.features)) +
              (f"training examples" if is_train else f"validation samples"))

    def __getitem__(self, index):
        return (self.features[index].float(), self.labels[index])

    def __len__(self):
        return len(self.features)


def load_data_bananas(batch_size):
    """
    加载香蕉检测数据集
    """
    train_iter = data.DataLoader(BananasDataset(
        is_train=True), batch_size, shuffle=True)
    val_iter = data.DataLoader(BananasDataset(
        is_train=False), batch_size, shuffle=False)
    return train_iter, val_iter


def read_voc_images(voc_dir: str, is_train=True):
    """读取所有的VOC图像并进行标注"""
    # 从TXT文件中读取
    txt_fname = os.path.join(
        voc_dir, "ImageSets", "Segmentation", "train.txt" if is_train else "val.txt")
    mode = tv.io.image.ImageReadMode.RGB

    with open(txt_fname, "r") as f:
        images = f.read().split()
    features, labels = [], []
    # 循环读取所有的图片和它们的标签
    for i, fname in enumerate(images):
        features.append(
            tv.io.read_image(os.path.join(
                voc_dir, "JPEGImages", f"{fname}.jpg"
            ), mode)
        )
        labels.append(
            tv.io.read_image(os.path.join(
                voc_dir, "SegmentationClass", f"{fname}.png"
            ), mode)
        )
    return features, labels


# 定义颜色所代表的的类别
VOC_COLORMAP = [[0, 0, 0], [128, 0, 0], [0, 128, 0], [128, 128, 0],
                [0, 0, 128], [128, 0, 128], [0, 128, 128], [128, 128, 128],
                [64, 0, 0], [192, 0, 0], [64, 128, 0], [192, 128, 0],
                [64, 0, 128], [192, 0, 128], [64, 128, 128], [192, 128, 128],
                [0, 64, 0], [128, 64, 0], [0, 192, 0], [128, 192, 0],
                [0, 64, 128]]
VOC_CLASSES = ['background', 'aeroplane', 'bicycle', 'bird', 'boat',
               'bottle', 'bus', 'car', 'cat', 'chair', 'cow',
               'diningtable', 'dog', 'horse', 'motorbike', 'person',
               'potted plant', 'sheep', 'sofa', 'train', 'tv/monitor']
# 下面两个函数实现颜色和类别的相互映射


def voc_colormap2label():
    """
    构建从RGB到VOC类别索引的映射
    """
    colormap2label = t.zeros(256**3, dtype=t.long)
    for i, colormap in enumerate(VOC_COLORMAP):
        colormap2label[
            (colormap[0]*256+colormap[1])*256 + colormap[2]
        ] = i
    return colormap2label


def voc_label_indeces(colormap: t.Tensor, colormap2label: t.Tensor):
    """
    将VOC标签中的RGB值映射到它们的类别索引
    """
    colormap = colormap.permute(1, 2, 0).numpy().astype("int32")
    idx = ((colormap[:, :, 0]*256 + colormap[:, :, 1])*256 + colormap[:, :, 2])
    return colormap2label[idx]


def voc_rand_crop(feature, label, height, width):
    """
    随机裁剪特征和标签图像
    """
    rect = tv.transforms.RandomCrop.get_params(feature, (height, width))
    feature = tv.transforms.functional.crop(feature, *rect)
    label = tv.transforms.functional.crop(label, *rect)
    return feature, label


class VOCSegDataset(t.utils.data.Dataset):
    """
    一个用于加载VOC数据集的自定义数据集
    """

    def __init__(self, is_train, crop_size, voc_dir):
        # 定义transform和裁剪尺寸
        self.transform = tv.transforms.Normalize(
            mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        self.crop_size = crop_size
        # 读取所有训练集或者测试集的图片
        features, labels = read_voc_images(voc_dir, is_train=is_train)
        # 把图片进行归一化并过滤掉不符合尺寸的图片
        self.features = [self.normalize_image(
            feature) for feature in self.filter(features)]

        self.labels = self.filter(labels)
        self.colormap2label = voc_colormap2label()
        print(f"read {len(self.features)} examples")

    def normalize_image(self, imgs: t.Tensor):
        """
        将图片进行归一化,转成0-1
        """
        return self.transform.forward(imgs.float()/255)

    def filter(self, imgs: t.Tensor):
        """
        去掉尺寸不符合的图片
        """
        return [img for img in imgs if(
            img.shape[1] >= self.crop_size[0] and img.shape[2] >= self.crop_size[1]
        )]

    def __getitem__(self, idx: int):
        """
        继承自Dataset类
        """
        feature, label = voc_rand_crop(
            self.features[idx], self.labels[idx], *self.crop_size)
        return (feature, voc_label_indeces(label, self.colormap2label))

    def __len__(self):
        return len(self.features)


def load_data_voc(voc_dir, batch_size, crop_size, num_workers=0):
    """
    加载VOC语义分割数据集
    """
    assert batch_size > 0
    if voc_dir is None:
        voc_dir = download_extract(
            "voc2012", os.path.join("VoCdevkit", "VOC2012"))

    train_set = VOCSegDataset(True, crop_size, voc_dir)
    test_set = VOCSegDataset(False, crop_size, voc_dir)

    train_iter = data.DataLoader(
        train_set, batch_size, num_workers=num_workers, drop_last=True)
    test_iter = data.DataLoader(
        test_set, batch_size, num_workers=num_workers, drop_last=True)

    return train_iter, test_iter


# CONSTANT AND LAMBDA EXPRESSIONS
numpy = lambda x, *args, **kwargs: x.detach().numpy(*args, **kwargs)
size = lambda x, *args, **kwargs: x.numel(*args, **kwargs)
reshape = lambda x, *args, **kwargs: x.reshape(*args, **kwargs)
to = lambda x, *args, **kwargs: x.to(*args, **kwargs)
reduce_sum = lambda x, *args, **kwargs: x.sum(*args, **kwargs)
argmax = lambda x, *args, **kwargs: x.argmax(*args, **kwargs)
astype = lambda x, *args, **kwargs: x.type(*args, **kwargs)
transpose = lambda x, *args, **kwargs: x.t(*args, **kwargs)
reduce_mean = lambda x, *args, **kwargs: x.mean(*args, **kwargs)

# URL
DATA_HUB = dict()
DATA_URL = 'http://d2l-data.s3-accelerate.amazonaws.com/'
DATA_HUB['kaggle_house_train'] = (
    DATA_URL + 'kaggle_house_pred_train.csv', '585e9cc93e70b39160e7921475f9bcd7d31219ce')
DATA_HUB['kaggle_house_test'] = (
    DATA_URL + 'kaggle_house_pred_test.csv', 'fa19780a7b011d9b009e8bff8e99922a8ee2eb90')
DATA_HUB['airfoil'] = (DATA_URL + 'airfoil_self_noise.dat',
                       '76e5be1548fd8222e5074cf0faae75edff8cf93f')
DATA_HUB['time_machine'] = (
    DATA_URL + 'timemachine.txt', '090b5e7e70c295757f55df93cb0a180b9691891a')
DATA_HUB['fra-eng'] = (DATA_URL + 'fra-eng.zip',
                       '94646ad1522d915e7b0f9296181140edcf86a4f5')
DATA_HUB['hotdog'] = (DATA_URL + 'hotdog.zip',
                      'fba480ffa8aa7e0febbb511d181409f899b9baa5')
DATA_HUB['banana-detection'] = (DATA_URL + 'banana-detection.zip',
                                '5de26c8fce5ccdea9f91267273464dc968d20d72')
DATA_HUB['voc2012'] = (DATA_URL + 'VOCtrainval_11-May-2012.tar',
                       '4e443f8a2eca6b1dac8a6c57641b67dd40621a49')
