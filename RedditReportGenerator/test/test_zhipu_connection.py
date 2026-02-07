"""测试智谱 AI API 连接"""
import os
from openai import OpenAI

# 设置智谱 AI 的 API 信息
api_key = "8c64dae9d2c440cf8f2892433cb7337c.86PTjcxTrjPI5oX0"
base_url = "https://open.bigmodel.cn/api/paas/v4"
model = "glm-4-flash-250414"

print(f"API Key: {api_key[:20]}...")
print(f"Base URL: {base_url}")
print(f"Model: {model}")

try:
    # 尝试创建 OpenAI 客户端
    client = OpenAI(api_key=api_key, base_url=base_url)

    # 测试简单请求
    print("\n测试模型信息...")
    try:
        model_info = client.models.retrieve(model)
        print(f"模型信息: {model_info}")
    except Exception as e:
        print(f"获取模型信息失败: {e}")

    # 测试聊天补全
    print("\n测试聊天补全...")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": "你好，请简单介绍一下你自己。"}
        ],
        temperature=0.7,
        max_tokens=100,
    )

    print(f"成功获取响应: {response.choices[0].message.content}")

    print("\n智谱 AI API 连接测试成功!")

except Exception as e:
    print(f"\n智谱 AI API 连接失败: {e}")
    print(f"\n错误类型: {type(e).__name__}")
    print(f"错误详情: {str(e)}")
