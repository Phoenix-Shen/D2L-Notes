# 又是一个船新版本的Transformer

NLP从入门到放弃o(╥﹏╥)o

我觉得我像LSTM中的short term memory，鱼的记忆，又忘记了，又来敲一遍复习一下哦，这次是wmathor的版本[链接在此](https://wmathor.com/index.php/archives/1438/),这里是详细的解析[链接](https://wmathor.com/index.php/archives/1455/)

## 网络架构和特性

1. 全注意力(Attention is All You Need)
2. 位置编码，RNN有天然的时间信息，但是在Transformer里面我们没有位置信息，所以要加入位置编码，这个位置编码是不训练的，但是在BERT里面它是需要训练的
3. 自注意力和内积(Dot-Product,KQV之类的玩意)
4. 多头自注意力
5. 残差连接和Layer Norm
6. 整体是经典的Encoder-Decoder架构,但是Encoder有很多层，在原来论文中是6个Encoder，最后将输出传到Decoder里面去，他很像Seq2Seq但是它没有任何RNN的成分
7. 不同于LSTM，它是并行训练的，而非LSTM这种串行训练
8. Masked Self-Attention:防止ground truth暴露在Decoder里面

## 1. Encoder

### 1. Positional Encoding 位置编码

为什么我们要在词嵌入向量上面加入位置编码？这是因为Transformer抛弃了传统RNN通过时间进行传播的架构，所以需要一个东西来补偿我们输入中的`序列关系`,这个东西就是`位置嵌入`。

如果采用均匀分布，给每个嵌入加上一个数字，那么句子长度90和30的向量每一个字符之间的差值是不一样的，这将导致歧义。

如果直接加上1、2、3、4等数字，可能会覆盖掉原来的特征，所以我们会导致模型学不到东西。

理想情况下，我们需要满足以下条件：

- 每个字的编码都是唯一的，这个很好理解
- 不同长度的句子之间，任何两个字之间的差距应该是一致的，否则会导致歧义
- 它的值是有界的，否则会导致模型学不倒东西

使用正弦余弦的位置编码便可以满足上述需求，它将与句子的嵌入向量`相加`，起到`增强输入`的作用。

位置嵌入函数的周期从2pi到10000*2pi变化，从而产生独一的纹理位置信息，最终使得模型学习到位置之间的依赖关系和自然语言的时序特性。

### 2. 自注意力机制

- 使用矩阵运算加快速度

    对于输入的句子$\mathbf{X}$，我们通过wordEmbedding得到句子中的每个字的字向量，然后再加上位置编码进行一个位置信息的融合，然后得到了该字的真正的向量表示，我们假设第$t$个字的向量为$x_t$

    然后我们有三个转换矩阵$W_Q,W_K,W_V$，这三个矩阵分别对字向量进行三次线性变换，于是从$x_t$中衍生出来三个新的向量$q_t,k_t,v_t.$，将所有的$q_t.$拼成一个矩阵$Q$，称为查询矩阵，同理将所有的$k_t.$拼成一个矩阵，记作键矩阵$K$，将所有的$v_t.$拼成一个矩阵，记作键矩阵$V$。

    为了取得注意力权重，我们使用查询向量$q_1$来乘以矩阵$K$，这样就得到了第一个向量与其它（包括他自己）的注意力分数（attention score），然后再经过softmax，来获得真正的注意力权重(attention weight)

    有了权重之后，把权重给乘以矩阵$V$，就得到了输出。

    所谓的SelfAttention就是KQV都是一个东西，就叫自注意力；在Transformer中，我们不需要像RNN那样串行运算，所以可以将上文的形式增广成一个矩阵，我们使用矩阵$Q$乘以矩阵$K$，就得到了所有字的注意力分数，进行softmax操作之后就得到了所有的权重。

- 使用多头注意力
    为什么需要使用多头注意力(MHA)，参考[知乎文章](https://zhuanlan.zhihu.com/p/387373100)

    模型在对当前位置的信息进行编码的时候，会过度地将注意力集中在自身的位置（虽然符合常识），但是它忽略了其它的位置，所以作者采取了一种方式叫做多头注意力，它能够缓解上述问题。

    使用多头注意力能够给予注意力层的输出包含有不同子空间的编码表示信息，从而增强模型的表达能力

    在实际的代码中，我们还是使用`矩阵运算`来`加速多头注意力`，具体的请查看代码

- 进行使用padding mask避免算到\<pad\>这种无效的词

    在实际计算注意力权重的过程中，我们不应该计算padding与任何字的attention，所以将这部分矩阵的值使用负无穷来替代，这样Softmax操作下来，相应位置的值就是0了

### 3. 残差连接和层归一化 Layer Norm

- 残差连接

    直接将加了位置编码的嵌入向量与计算出来的自注意力进行相加，这就是残差连接

- 层归一化

    由于在batch中，我们可能存在不一样长度的句子，这样下来BatchNorm就没有办法去做了，这样我们改成层归一化LayerNorm将矩阵的列为单位求mean和variance

### 4. 整体架构

- 字向量和位置编码
    句子进来之后使用nn.Embedding来进行编码，然后加上位置编码

- 多头自注意力机制
    使用多个注意力头来对编码之后的嵌入向量进行处理，然后使用线性层来归一化维度。

- 残差连接和层归一化
    使用残差连接学习恒等映射，加上层归一化能够增加收敛速度

- 前馈网络+add&Norm
    两层线性映射，加上ReLU函数进行激活

## 2. Decoder

### 1. 带有掩膜的自注意力

    我们看不到未来的词，所以不应该将所有的ground truth暴露在解码器中，我们需要对解码器的输入进行一些处理，这就是所谓的Mask，具体操作为将注意力分数矩阵的上三角全部用负无穷去替换。

### 2. 带有掩膜的编码器-解码器注意力

    与1不同的是，我们KV来自于编码器，其余的都一样

## 3. 相比于D2L的版本

少了一些转置操作，能够更加方便地去理解。

## 4. 关于PaddingMask的问题

如果是一个带有padding的句子，应该padding之后得到的mask应该是有padding的行和列都为True(有padding存在)，为什么在这里我们只填充了列为True而不是相关的行列都为True呢？

这里只要保证最后一列为True就行辣，因为Padding对于其它的词语的注意力是灭有意义的，而在正常词语当中，我们不希望我们的注意力被Padding所影响，所以是一定要在列上填充为True，至于有Padding的行，我们不关心他算出来的是什么东西，所以加不加都无所谓，严格地来说是要加的，代码中偷懒了，没有加。
