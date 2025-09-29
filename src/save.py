# from transformers import AutoTokenizer, AutoModelForSequenceClassification
# import torch

# # 指定本地模型路径
# model_name = "/home/believe/.cache/modelscope/hub/models/iic/nlp_structbert_sentiment-classification_chinese-base"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModelForSequenceClassification.from_pretrained(model_name)

# # 测试句子
# test_sentences = [
#     "这部电影太精彩了，我完全被情节吸引住了！",
#     "今天天气真好，心情特别愉快。",
#     "我刚刚完成了一个重要的项目，感觉非常有成就感。",
#     "这家餐厅的食物非常美味，服务也很好。",
#     "我收到了一份意外的礼物，感到非常惊喜和开心。",
#     "这部电影太让人失望了，情节毫无新意。",
#     "今天天气真糟糕，一直下雨，心情很糟糕。",
#     "我刚刚错过了一班重要的火车，感觉非常沮丧。",
#     "这家餐厅的食物很难吃，服务也很差。",
#     "我遇到了一个很不愉快的客户，感觉非常生气和无助。",
#     "今天天气很普通，没有什么特别的。",
#     "我刚刚完成了一个常规的任务，感觉很平常。",
#     "这家餐厅的食物还可以，没有特别好也没有特别差。",
#     "我今天没有遇到什么特别的事情，一切都很平静。",
#     "这部电影的情节很一般，没有太多亮点。",
#     "这部电影有些地方很精彩，但整体感觉有点拖沓。",
#     "今天天气不错，但交通很拥堵，让我有些烦躁。",
#     "我刚刚完成了一个项目，虽然有些地方做得不错，但整体感觉还有提升的空间。",
#     "这家餐厅的食物味道不错，但价格有点贵。",
#     "我今天收到了一份礼物，虽然很高兴，但也有点意外。"
# ]

# # 进行情感分析
# def analyze_sentiment(sentences):
#     results = []
#     for sentence in sentences:
#         # 对句子进行分词
#         inputs = tokenizer(sentence, return_tensors="pt", padding=True, truncation=True, max_length=512)
        
#         # 获取模型的预测结果
#         with torch.no_grad():
#             outputs = model(**inputs)
        
#         # 获取预测的情感类别
#         logits = outputs.logits
#         predicted_class = torch.argmax(logits, dim=1).item()
        
#         # 将预测结果转换为情感标签
#         sentiment_labels = ["负面", "中性", "正面"]
#         sentiment = sentiment_labels[predicted_class]
        
#         # 计算情感强度（置信度）
#         probabilities = torch.nn.functional.softmax(logits, dim=1)
#         confidence = probabilities[0][predicted_class].item()
        
#         results.append({
#             "句子": sentence,
#             "情感": sentiment,
#             "置信度": confidence
#         })
    
#     return results

# # 测试情感分析
# results = analyze_sentiment(test_sentences)

# # 打印结果
# for result in results:
#     print(f"句子: {result['句子']}")
#     print(f"情感: {result['情感']}")
#     print(f"置信度: {result['置信度']:.4f}")
#     print("-" * 50)

#模型下载
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

# 初始化情感分类管道
semantic_cls = pipeline(Tasks.text_classification, 'iic/nlp_structbert_emotion-classification_chinese-tiny', model_revision='v1.0.0')

# 测试输入
input_text = '新年快乐！'
result = semantic_cls(input={'text': input_text})

# 打印结果
print(result)