---
language:
- zh
tags:
- legal
size_categories:
- 100M<n<1B
license: apache-2.0
---


# DISC-Law-SFT Dataset

Legal Intelligent systems in Chinese require a combination of various abilities, including legal text understanding and generation. To achieve this, we have constructed a high-quality supervised fine-tuning dataset called DISC-Law-SFT, which covers different legal scenarios such as legal information extraction, legal judgment prediction, legal document summarization, and legal question answering. DISC-Law-SFT comprises two subsets, DISC-Law-SFT-Pair and DISC-Law-SFT-Triplet. The former aims to introduce legal reasoning abilities to the LLM, while the latter helps enhance the model's capability to utilize external legal knowledge. For more detailed information, please refer to our [technical report](https://arxiv.org/abs/2309.11325) or [paper](https://link.springer.com/chapter/10.1007/978-981-97-5569-1_19). The distribution of the dataset is:

<img src="" alt="" width=""/>

<table>
  <tr>
    <th>Dataset</th>
    <th>Task/Source</th>
    <th>Size</th>
    <th>Scenario</th>
  </tr>
  <tr>
    <td rowspan="10">DISC-Law-SFT-Pair</td>
    <td>Legal information extraction</td>
    <td>32K</td>
    <td rowspan="7">Legal professional assistant</td>
  </tr>
  <tr>
    <td>Legal event detection</td>
    <td>27K</td>
  </tr>
  <tr>
    <td>Legal case classification</td>
    <td>20K</td>
  </tr>
  <tr>
    <td>Legal judgement prediction</td>
    <td>11K</td>
  </tr>
  <tr>
    <td>Legal case matching</td>
    <td>8K</td>
  </tr>
  <tr>
    <td>Legal text summarization</td>
    <td>9K</td>
  </tr>
  <tr>
    <td>Judicial public opinion summarization</td>
    <td>6K</td>
  </tr>
  <tr>
    <td>Legal question answering</td>
    <td>93K</td>
    <td>Legal consultation services</td>
  </tr>
  <tr>
    <td>Legal reading comprehension</td>
    <td>38K</td>
    <td rowspan="2">Judicial examination assistant</td>
  </tr>
  <tr>
    <td>Judicial examination</td>
    <td>12K</td>
  </tr>
  <tr>
    <td rowspan="2">DISC-Law-SFT-Triple</td>
    <td>Legal judgement prediction</td>
    <td>16K</td>
    <td>Legal professional assistant</td>
  </tr>
  <tr>
    <td>Legal question answering</td>
    <td>23K</td>
    <td>Legal consultation services</td>
  </tr>
  <tr>
    <td rowspan="2">General</td>
    <td>Alpaca-GPT4</td>
    <td>48K</td>
    <td rowspan="2">General scenarios</td>
  </tr>
  <tr>
    <td>Firefly</td>
    <td>60K</td>
  </tr>
  <tr>
    <td>Total</td>
    <td colspan="3">403K</td>
  </tr>
</table>

We currently open-source most of the DISC-Law-SFT Dataset.

More detail and news check our [homepage](https://github.com/FudanDISC/DISC-LawLLM) !

## Citation

If our project has been helpful for your research and work, please kindly cite our work as follows:

```
@misc{yue2023disclawllm,
    title={DISC-LawLLM: Fine-tuning Large Language Models for Intelligent Legal Services}, 
    author={Shengbin Yue and Wei Chen and Siyuan Wang and Bingxuan Li and Chenchen Shen and Shujun Liu and Yuxuan Zhou and Yao Xiao and Song Yun and Xuanjing Huang and Zhongyu Wei},
    year={2023},
    eprint={2309.11325},
    archivePrefix={arXiv},
    primaryClass={cs.CL}
}

@inproceedings{yue2024lawllm,
  title={LawLLM: Intelligent Legal System with Legal Reasoning and Verifiable Retrieval},
  author={Yue, Shengbin and Liu, Shujun and Zhou, Yuxuan and Shen, Chenchen and Wang, Siyuan and Xiao, Yao and Li, Bingxuan and Song, Yun and Shen, Xiaoyu and Chen, Wei and others},
  booktitle={International Conference on Database Systems for Advanced Applications},
  pages={304--321},
  year={2024},
  organization={Springer}
}
```