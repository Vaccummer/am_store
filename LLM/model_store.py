import os
import math
import torch
import torch.nn as nn
from torch.nn import functional as F
from torch.utils.data import Dataset
from torch.cuda.amp import autocast as autocast
from transformers import AutoTokenizer
from kan_model import KANLayer
class Word_Embedding(nn.Module):
    def __init__(self, vocabulary_length, d_model) -> None:
        super().__init__()
        self.word_embedding_lookup_table = nn.Embedding(num_embeddings=vocabulary_length, embedding_dim=d_model)
    def forward(self, x):
        return self.word_embedding_lookup_table(x)


class Position_Embedding(nn.Module):
    def __init__(self, context_length, d_model, device='cuda') -> None:
        super().__init__()
        self.position_encoding_lookup_table = torch.zeros(context_length, d_model)
        position = torch.arange(0, context_length, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        self.position_encoding_lookup_table[:, 0::2] = torch.sin(position * div_term)
        self.position_encoding_lookup_table[:, 1::2] = torch.cos(position * div_term)
        self.position_encoding_lookup_table = self.position_encoding_lookup_table.to(device)
        
    
    def forward(self, x):
        B, T = x.shape
        return self.position_encoding_lookup_tabl[:T, :]


class Embedding1(nn.Module):
    # word_embedding as a cached table
    def __init__(self, vocabulary_length, d_model, context_length, **kwargs):
        super().__init__()
        self.word_embedding_lookup_table = nn.Embedding(num_embeddings=vocabulary_length, embedding_dim=d_model)
        position_encoding_lookup_table = torch.zeros(context_length, d_model)
        position = torch.arange(0, context_length, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        position_encoding_lookup_table[:, 0::2] = torch.sin(position * div_term)
        position_encoding_lookup_table[:, 1::2] = torch.cos(position * div_term)
        # position_encoding_lookup_table = position_encoding_lookup_table.to(deivce)
        self.register_buffer('position_encoding_lookup_table', position_encoding_lookup_table)
        
        # self.register_buffer('mask', mask)
    def forward(self, x):
        B, T = x.shape
        position_embedding  = self.position_encoding_lookup_table[:T, :].unsqueeze(0).expand(B, -1, -1)
        x = self.word_embedding_lookup_table(x) + position_embedding
        return x


class Embedding(nn.Module):
    # word_embedding as a layer
    def __init__(self, vocabulary_length, d_model, context_length, **kwargs):
        super().__init__()
        self.word_embedding = nn.Embedding(num_embeddings=vocabulary_length, embedding_dim=d_model)
        self.context_length = context_length
        position_encoding_lookup_table = torch.zeros(context_length, d_model)
        position = torch.arange(0, context_length, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).half() * (-math.log(10000.0) / d_model))
        position_encoding_lookup_table[:, 0::2] = torch.sin(position * div_term)
        position_encoding_lookup_table[:, 1::2] = torch.cos(position * div_term)
        position_encoding_lookup_table = position_encoding_lookup_table
        self.register_buffer('position_encoding_lookup_table', position_encoding_lookup_table)
        
        # self.register_buffer('mask', mask)
    def forward(self, x):
        x = x.reshape(-1, self.context_length)
        B, T = x.shape
        x = self.word_embedding(x) + self.position_encoding_lookup_table[:T, :].unsqueeze(0).expand(B, -1, -1)
        # mask = torch.tril(torch.ones((T, T, ), dtype=torch.int8, requires_grad=False)).bool()
        return x

class WordEmbedding(nn.Module):
    def __init__(self, d_model, vocabulary_length, **kwargs) -> None:
        super().__init__()
        self.word_embedding = nn.Embedding(num_embeddings=vocabulary_length, embedding_dim=d_model)
    def forward(self, x):
        return self.word_embedding(x)

class FeedForward(nn.Module):
    def __init__(self, in_features: int, inter_features:int, out_features:int=-1, activation_func=F.silu, dropout: float = 0.1):
        super().__init__()
        out_features = out_features if out_features != -1 else in_features
        self.l1 = nn.Linear(in_features=in_features, out_features=inter_features)  # col p
        self.l2 = nn.Linear(in_features=inter_features, out_features=out_features)  # row p
        self.dropout = nn.Dropout(dropout)
        self.activation_func = activation_func
    def forward(self, x):
        return self.dropout(self.l2(self.activation_func(self.l1(x))))


class FeedForwardLlama(nn.Module):
    def __init__(self, in_features: int, inter_features:int, out_features:int=-1, activation_func=F.silu, dropout: float = 0.1):
        super().__init__()
        out_features = out_features if out_features != -1 else in_features
        self.l1 = nn.Linear(in_features=in_features, out_features=inter_features)  
        self.l2 = nn.Linear(in_features=inter_features, out_features=out_features)  
        self.l3 = nn.Linear(in_features=in_features, out_features=inter_features)  

        self.dropout = nn.Dropout(dropout)
        self.activation_func = activation_func
    def forward(self, x):
        return self.l2(self.activation_func(self.l1(x)) * self.l3(x))


class Attention(nn.Module):
    # single head attention layer
    # input has the shape of [Batch size, context_length, d_model]
    # output has the shape of [Batch size, context_length, d_model//heads_num]
    def __init__(self, d_model:int, heads_num:int, context_length:int, mask, **kwargs):
        super().__init__()
        head_size = d_model//heads_num
        self.key = nn.Linear(in_features=d_model, out_features=head_size, bias=False)     # col p
        self.query = nn.Linear(in_features=d_model, out_features=head_size, bias=False)   # col p
        self.value = nn.Linear(in_features=d_model, out_features=head_size, bias=False)   # col p
        # mask = torch.arange(context_length).unsqueeze(1) <= torch.arange(context_length).unsqueeze(0)
        # self.register_buffer('tril', torch.tril(torch.ones((context_length, context_length, ), dtype=torch.int8)).bool())  # Lower triangular mask
        # self.register_buffer('mask', mask)
        # torch.tril(torch.ones((context_length, context_length, ), device='cpu'))
        self.d_model = d_model 
        self.head_size = head_size
        self.context_length = context_length
        self.register_buffer('mask', mask)

    def forward(self, x):
        B, T, C = x.shape  # Batch size, Time steps(current context_length), Channels(dimensions)
        assert T <= self.context_length
        assert C == self.d_model
        q = self.query(x)
        k = self.key(x)
        v = self.value(x)

        # Scaled dot product attention: Q @ K^T / sqrt(d_k)
        weights = (q @ k.transpose(-2, -1)) * (1.0 / math.sqrt(k.size(-1)))
        weights = weights.masked_fill(self.mask[:T, :T] == 0, float('-inf'))
        weights = F.softmax(input=weights, dim=-1)
        out = weights @ v
        return out


class AttentionTP(nn.Module):
    def __init__(self, d_model:int, context_length:int, heads_num:int, eps:float, **kwargs):
        super().__init__()
        self.head_dim = d_model // heads_num
        self.heads_num = heads_num
        self.wq = nn.Linear(d_model, self.heads_num * self.head_dim, bias=False)
        self.wk = nn.Linear(d_model, self.heads_num * self.head_dim, bias=False)
        self.wv = nn.Linear(d_model, self.heads_num * self.head_dim, bias=False)

        self.wo = nn.Linear(heads_num * self.head_dim, d_model, bias=False)
    def forward(self, x):
        print(x.shape)
        bsz, seqlen, _ = x.shape
        xq, xk, xv = self.wq(x), self.wk(x), self.wv(x)
        xq = xq.view(bsz, seqlen, self.heads_num, self.head_dim)
        xk = xk.view(bsz, seqlen, self.heads_num, self.head_dim)
        xv = xv.view(bsz, seqlen, self.heads_num, self.head_dim)
        
        xq = xq.transpose(1, 2)  # (bs, n_local_heads, seqlen, head_dim)
        xk = xk.transpose(1, 2)  # (bs, n_local_heads, seqlen, head_dim)
        xv = xv.transpose(1, 2)  # (bs, n_local_heads, seqlen, head_dim)

        output = F.scaled_dot_product_attention(xq, xk, xv, is_causal=True)
        output = output.transpose(1, 2).contiguous()  # (bs, seqlen, n_local_heads, head_dim)
        output = output.view(bsz, seqlen, -1)
        return self.wo(output)


class MultiHeadAttention(nn.Module):
    # multi heads of attention layer, higher lever wrap of Attention layer
    def __init__(self, d_model:int, context_length:int, heads_num:int, mask:torch.Tensor, **kwargs):
        super().__init__()
        self.head_size = d_model//heads_num
        para_dict = {"d_model":d_model, "context_length":context_length, "heads_num":heads_num}
        self.heads = nn.ModuleList([Attention(**para_dict, mask=mask) for _ in range(heads_num)])

    def forward(self, x):
        out = torch.cat([h(x) for h in self.heads], dim=-1)
        return out


class TransformerBlock(nn.Module):
    # transformer block which rely on Attention layer
    def __init__(self, d_model:int, context_length:int, heads_num:int, mask:torch.Tensor, dropout:float=0.1, **kwargs):
        super().__init__()
        para_dict = {"d_model":d_model, "context_length":context_length, "heads_num":heads_num, "dropout":dropout}
        self.head_size = d_model//heads_num
        self.context_length = context_length
        self.mask = mask
        self.heads_num = heads_num
        
        self.heads = [Attention(**para_dict, mask=mask) for _ in range(heads_num)]

        self.feed_forward = FeedForward(in_features=d_model, inter_features=4*d_model, dropout=dropout)
        self.dropout = nn.Dropout(dropout)
        
        self.layer_norm_1 = nn.LayerNorm(normalized_shape=d_model)
        
        self.layer_norm_2 = nn.LayerNorm(normalized_shape=d_model)

    def forward(self, x,):
        # weights = (q @ k.transpose(-2, -1)) * (1.0 / math.sqrt(k.size(-1)))
        # weights = weights.masked_fill(self.mask[:T, :T] == 0, float('-inf'))
        # weights = F.softmax(input=weights, dim=-1)
        # weights = self.dropout_layer(weights)
        #out = weights @ v
        x = x + torch.cat([h(self.layer_norm_1(x)) for h in self.heads], dim=-1)
        x = x + self.dropout(self.feed_forward(self.layer_norm_2(x)))
        return x


class RMSNorm(torch.nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def _norm(self, x):
        return x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)

    def forward(self, x):
        output = self._norm(x.float()).type_as(x)
        return output 
    

class TransformerBlockPipe(nn.Module):
    # transformer_block independent of any attention layers
    # mask is transferred from former blocks to the later
    def __init__(self, d_model:int, context_length:int, heads_num:int, dropout:float=0.1, eps:float=1e-6, **kwargs):
        super().__init__()
        
        self.head_size = d_model//heads_num
        self.context_length = context_length
        self.heads_num = heads_num
        
        self.wks = nn.ModuleList([nn.Linear(in_features=d_model, out_features=self.head_size, bias=False) for _ in range(heads_num)])
        self.wqs = nn.ModuleList([nn.Linear(in_features=d_model, out_features=self.head_size, bias=False) for _ in range(heads_num)])
        self.wvs = nn.ModuleList([nn.Linear(in_features=d_model, out_features=self.head_size, bias=False) for _ in range(heads_num)])


        self.feed_forward = FeedForwardLlama(in_features=d_model, inter_features=4*d_model, dropout=dropout)
        self.attention_norm =  RMSNorm(dim=context_length, eps=eps)
        self.ffn_norm = RMSNorm(dim=d_model, eps=eps)

    def forward(self, x_ori):
        mask = torch.tril(torch.ones((self.context_length, self.context_length, ), dtype=torch.int8, requires_grad=False)).bool()
        x = self.attention_norm(x_ori)
        mask = mask.to(x.device)
        ouputs = []
        for i in range(self.heads_num):
            q = self.wqs[i](x)
            k = self.wks[i](x)
            v = self.wvs[i](x)
            B, T, C = x.shape  # Batch size, Time steps(current context_length), Channels(dimensions)
            weights = (q @ k.transpose(-2, -1)) * (1.0 / math.sqrt(k.size(-1)))
            weights = weights.masked_fill(mask[:T, :T] == 0, float('-inf'))
            weights = F.softmax(input=weights, dim=-1)
            out = weights @ v
            ouputs.append(out)
        ouputs = x_ori + torch.cat(ouputs, dim=-1)
        x_ori = None
        ouputs = ouputs + self.feed_forward(self.ffn_norm(ouputs))
        return ouputs


class TransformerBlockDS(nn.Module):
    # transformer_block independent of any attention layers
    # mask is transferred from former blocks to the later
    def __init__(self, d_model:int, context_length:int, heads_num:int, dropout:float=0.1, eps:float=1e-6, **kwargs):
        super().__init__()
        
        self.head_size = d_model//heads_num
        self.context_length = context_length
        self.heads_num = heads_num
        
        self.wks = nn.ModuleList([nn.Linear(in_features=d_model, out_features=self.head_size, bias=False) for _ in range(heads_num)])
        self.wqs = nn.ModuleList([nn.Linear(in_features=d_model, out_features=self.head_size, bias=False) for _ in range(heads_num)])
        self.wvs = nn.ModuleList([nn.Linear(in_features=d_model, out_features=self.head_size, bias=False) for _ in range(heads_num)])


        self.feed_forward = FeedForwardLlama(in_features=d_model, inter_features=4*d_model, dropout=dropout)
        self.attention_norm =  RMSNorm(dim=context_length, eps=eps)
        self.ffn_norm = RMSNorm(dim=d_model, eps=eps)

    def forward(self, x_ori, mask=None):
        if mask=='None':
            mask = torch.tril(torch.ones((self.context_length, self.context_length, ), dtype=torch.int8, requires_grad=False)).bool()
        x = self.attention_norm(x_ori)
        mask = mask.to(x.device)
        ouputs = []
        for i in range(self.heads_num):
            q = self.wqs[i](x)
            k = self.wks[i](x)
            v = self.wvs[i](x)
            B, T, C = x.shape  # Batch size, Time steps(current context_length), Channels(dimensions)
            weights = (q @ k.transpose(-2, -1)) * (1.0 / math.sqrt(k.size(-1)))
            weights = weights.masked_fill(mask[:T, :T] == 0, float('-inf'))
            weights = F.softmax(input=weights, dim=-1)
            out = weights @ v
            ouputs.append(out)
        ouputs = x_ori + torch.cat(ouputs, dim=-1)
        ouputs = ouputs + self.feed_forward(self.ffn_norm(ouputs))
        return ouputs, mask


class TransformerBlockTP(nn.Module):
    def __init__(self, d_model:int, context_length:int, heads_num:int, dropout:float=0.1, eps:float=1e-6, **kwargs):
        super().__init__()
        self.attention_norm = RMSNorm(dim=context_length, eps=eps)
        self.attention = AttentionTP(d_model=d_model, context_length=context_length, heads_num=heads_num, eps=eps)
        self.feed_forward = FeedForwardLlama(in_features=d_model, inter_features=4*d_model, dropout=dropout)
        self.ffn_norm = RMSNorm(dim=d_model, eps=eps)
    def forward(self, x):
        x = self.attention_norm(x)
        x = x + self.attention(x)
        x = x + self.feed_forward(self.ffn_norm(x))
        return x


class Model_Out_Layer(nn.Module):
    # linear projection from d_model to vocab_size
    def __init__(self, d_model:int, vocabulary_length:int, eps:float=1e-6, **kwargs):
        super().__init__()
        self.language_model_out_linear_layer = nn.Linear(in_features=d_model, out_features=vocabulary_length)
        # self.language_model_out_linear_layer = KANLayer(input_dim=d_model, output_dim=vocabulary_length).to(1)
        self.norm = RMSNorm(dim=vocabulary_length, eps=eps)
        
    def forward(self, x):
        x = self.norm(self.language_model_out_linear_layer(x))
        return x


class CrossEntropyLoss(nn.Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, input_f):
        logits, targets = input_f
        if not targets:
            return logits
        B, T, C = logits.shape
        logits = logits.view(B * T, C)
        targets = targets.view(B * T)
        loss = F.cross_entropy(input=logits, target=targets)
        logits= None
        targets = None
        return loss


class Transformer_LLM_MP(nn.Module):
    # transformer_llm module, consist of Embedding, TransformerBlock(Attention), Model_Out_Layer
    # output is prediction, no loss calculation
    # used for mannul set Model Parallism
    def __init__(self, d_model:int, context_length:int, batch_size:int, vocabulary_length:int, blocks_num:int, heads_num:int, chunk:int, dropout:float=0.1, **kwargs) -> None:
        super().__init__()
        para_dict = {"d_model":d_model, "vocabulary_length":vocabulary_length,"context_length":context_length, "heads_num":heads_num, "dropout":dropout}
        self.chunk = chunk
        self.batch_size = batch_size
        self.embedding = Embedding(**para_dict)
        # self.out_layer = Model_Out_Layer(**para_dict)
        mask0 = torch.tril(torch.ones((context_length, context_length, ), dtype=torch.int8)).bool().to(0)
        mask1 = torch.tril(torch.ones((context_length, context_length, ), dtype=torch.int8)).bool().to(1)
        mask2 = torch.tril(torch.ones((context_length, context_length, ), dtype=torch.int8)).bool().to(2)
        mask3 = torch.tril(torch.ones((context_length, context_length, ), dtype=torch.int8)).bool().to(3)

        # self.part0 = nn.Sequential(self.embedding, TransformerBlock(**para_dict, mask=mask0), TransformerBlock(**para_dict, mask=mask0)).to('cuda:0')
        transformer_blocks0 = [TransformerBlock(**para_dict, mask=mask0) for i in range(1)]
        transformer_blocks1 = [TransformerBlock(**para_dict, mask=mask1) for i in range(2)]
        transformer_blocks2 = [TransformerBlock(**para_dict, mask=mask2) for i in range(2)]
        transformer_blocks3 = [TransformerBlock(**para_dict, mask=mask3) for i in range(1)]

        self.part0 = nn.Sequential(*([self.embedding] + transformer_blocks0)).to('cuda:0')
        self.part1 = nn.Sequential(*transformer_blocks1).to('cuda:1')
        self.part2 = nn.Sequential(*transformer_blocks2).to('cuda:2')
        self.part3 = nn.Sequential(*(transformer_blocks3+[Model_Out_Layer(**para_dict)])).to('cuda:3')
        # self.part3 = Model_Out_Layer(**para_dict).to('cuda:3')
    
    def forward(self, x):
        logit_l = []
        splits = iter(x.split(self.batch_size//self.chunk, dim=0))
        output_0= self.part0(next(splits)).to(1)
        output_1= self.part1(self.part0(next(splits)).to(1)).to(2)
        output_2= self.part2(self.part1(self.part0(next(splits)).to(1)).to(2)).to(3)

        for i in range(self.chunk-3):
            logit_i = self.part3(output_2)
            output_2 = self.part2(output_1).to(3)
            output_1 = self.part1(output_0).to(2)
            output_0 = self.part0(next(splits)).to(1)
            logit_l.append(logit_i.to('cpu'))
        
        logit_l.append(self.part3(output_2).to('cpu'))
        logit_l.append(self.part3(self.part2(output_1).to(3)).to('cpu'))
        logit_l.append(self.part3(self.part2(self.part1(output_0).to(2)).to(3)).to('cpu'))
        return torch.cat(logit_l, dim=0)


class Transformer_LLM(nn.Module):
    def __init__(self, hyperpara_dict:dict):
        super().__init__()
        self.hyperpara_dict = hyperpara_dict   
        for key_i, value_i in hyperpara_dict.items():
            setattr(self, key_i, value_i)

        # Set up token embedding look-up table
        self.token_embedding_lookup_table = nn.Embedding(num_embeddings=self.max_token_value + 1, embedding_dim=self.d_model)
        
        # calculate position embedding
        self.position_encoding_lookup_table = self.calculate_position_embedding().to(self.device) 

        # Different from original paper, here we add a final layer norm after all the blocks
        self.transformer_blocks = nn.Sequential(*(
                [TransformerBlock(self.hyperpara_dict) for _ in range(self.num_blocks)]
        ))


        self.language_model_out_linear_layer = nn.Linear(in_features=self.d_model, out_features=self.max_token_value)


        self.norm = nn.LayerNorm(normalized_shape=self.max_token_value)
    
    def forward(self, idx, targets=None):
        B, T = idx.shape
        x = self.token_embedding_lookup_table(idx) + self.position_encoding_lookup_table[:T, :]
        x = self.transformer_blocks(x)
        # The "logits" are the output values of our model before applying softmax
        logits = self.language_model_out_linear_layer(x)
        logits = self.norm(logits)

        if targets is not None:
            B, T, C = logits.shape
            logits_reshaped = logits.view(B * T, C)
            targets_reshaped = targets.view(B * T)
            loss = F.cross_entropy(input=logits_reshaped, target=targets_reshaped)
        else:
            loss = None
        return logits, loss
    
    def generate(self, idx, max_new_tokens):
        # idx is (B,T) array of indices in the current context
        for _ in range(max_new_tokens):
            # Crop idx to the max size of our positional embeddings table
            idx_crop = idx[:, -self.context_length:]
            # Get predictions
            logits, loss = self(idx_crop)
            # Get the last time step from logits where the dimensions of the logits are (B,T,C)
            logits_last_timestep = logits[:, -1, :]
            # Apply softmax to get probabilities
            probs = F.softmax(input=logits_last_timestep, dim=-1)
            # Sample from the probabilities' distribution.
            idx_next = torch.multinomial(input=probs, num_samples=1)
            # Append the sampled indexes idx_next to idx
            idx = torch.cat((idx, idx_next), dim=1)
        return idx

    
    def calculate_position_embedding(self):
        position_encoding_lookup_table = torch.zeros(self.context_length, self.d_model)
        position = torch.arange(0, self.context_length, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, self.d_model, 2).float() * (-math.log(10000.0) / self.d_model))
        position_encoding_lookup_table[:, 0::2] = torch.sin(position * div_term)
        position_encoding_lookup_table[:, 1::2] = torch.cos(position * div_term)
        # change position_encoding_lookup_table from (context_length, d_model) to (T, d_model)
        return position_encoding_lookup_table


class Mamba_LLM(nn.Module):
    def __init__(self, d_model:int, context_length:int, d_state:int, vocabulary_length:int, d_conv:int, expand:int, dropout:float=0.1, **kwargs):
        super().__init__()
        from mamba_ssm import Mamba2

        self.embedding = Embedding(vocabulary_length, d_model, context_length)

        self.mamba2 = Mamba2(d_model=d_model, d_state=d_state, d_conv=d_conv, expand=expand)

        self.out_layer = Model_Out_Layer(d_model, vocabulary_length)

        self.layer_norm = nn.LayerNorm(vocabulary_length)
    
    def forward(self, x, targets=None):
        x = self.embedding(x)
        x = self.mamba2(x)
        x = self.out_layer(x)
        x = self.layer_norm(x)
        if targets is not None:
            B, T, C = x.shape
            loss = F.cross_entropy(input=x.view(B*T, -1), target=targets.view(B*T))
            return loss
        return x


class AmengDataset(Dataset):
    def __init__(self, tokens:torch.Tensor, context_length:str, **kwargs) -> None:
        super().__init__()
        self.tokens = tokens
        self.context_length = context_length

    def __getitem__(self, index):
        x = self.tokens[:,index*self.context_length:(1+index)*self.context_length].view(-1).clone()
        y = self.tokens[:,1+index*self.context_length:1+(1+index)*self.context_length].view(-1).clone()
        return x, y
    
    def __len__(self):
        return (self.tokens.shape[-1]-1)//self.context_length - 1
    

def get_token(tokenizer_path, str_f):
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
    return tokenizer.encode(str_f)


class txt_train_data_manager:
    def __init__(self, txt_set_path='', txt_load_path='', tokens_path='', tokenizer_path='', **kwargs) -> None:
        self.txt_set_path = txt_set_path
        self.txt_load_path = txt_load_path
        self.tokens_path = tokens_path
        self.tokenizer_path = tokenizer_path
    
    def get_txt_list(self):
        from glob import glob
        txt_path_list = glob(os.path.join(self.txt_set_path, "**", "*.txt"), recursive=True)
        return txt_path_list

    def get_txt_data(self):
        from tools.functions import pkl
        if os.path.exists(self.txt_load_path):
            return pkl(self.txt_load_path)
        txt_path_list = self.get_txt_list
        txt_str = ''
        for txt_i in txt_path_list:
            with open(txt_i, 'r', encoding='utf-8') as f:
                    text_t = f.read()
                    txt_str += text_t[2000:-2000]
        pkl(self.txt_load_path, txt_str)
        return txt_str
        
    def get_tokens(self):
        if os.path.exists(self.tokens_path):
            return torch.load(self.tokens_path)
        txt_str = self.get_txt_data
        tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_path)
        len_s = tokenizer.max_len_single_sentence
        part_s = len(txt_str)//len_s
        from joblib import Parallel, delayed
        from copy import deepcopy
        tokens_l = Parallel(n_jobs=16, verbose=2)(delayed(get_token)(self.tokenizer_path, deepcopy(txt_str[i*len_s:(i+1)*len_s])) for i in range(part_s))
        return torch.cat(tokens_l, dim=0)


