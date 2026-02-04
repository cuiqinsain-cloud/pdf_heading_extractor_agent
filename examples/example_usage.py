"""
使用示例脚本
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agent import PDFHeadingExtractorAgent


def example_basic_usage():
    """基本使用示例"""
    print("=" * 60)
    print("示例1: 基本使用")
    print("=" * 60)

    # 初始化Agent
    agent = PDFHeadingExtractorAgent(config_path="config.yaml")

    # 提取标题（如果有示例PDF）
    # headings = agent.extract_headings("examples/sample.pdf")
    # print(f"提取了 {len(headings)} 个顶级标题")


def example_custom_format():
    """自定义输出格式示例"""
    print("\n" + "=" * 60)
    print("示例2: 自定义输出格式")
    print("=" * 60)

    agent = PDFHeadingExtractorAgent(config_path="config.yaml")

    # 输出为Markdown格式
    # headings = agent.extract_headings("examples/sample.pdf", output_format="markdown")


def example_get_dict():
    """获取字典格式结果"""
    print("\n" + "=" * 60)
    print("示例3: 获取字典格式")
    print("=" * 60)

    agent = PDFHeadingExtractorAgent(config_path="config.yaml")

    # 获取字典格式
    # result = agent.extract_to_dict("examples/sample.pdf")
    # print(result)


def example_batch_processing():
    """批量处理示例"""
    print("\n" + "=" * 60)
    print("示例4: 批量处理")
    print("=" * 60)

    agent = PDFHeadingExtractorAgent(config_path="config.yaml")

    # 批量处理多个PDF
    # pdf_files = ["file1.pdf", "file2.pdf", "file3.pdf"]
    # results = agent.batch_extract(pdf_files)
    #
    # for result in results:
    #     print(f"{result['pdf']}: {result['status']}")


def example_programmatic_usage():
    """编程式使用示例"""
    print("\n" + "=" * 60)
    print("示例5: 编程式使用")
    print("=" * 60)

    from src.pdf_parser import PDFParser
    from src.heading_detector import HeadingDetector
    from src.output_formatter import OutputFormatter
    import yaml

    # 加载配置
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 创建组件
    parser = PDFParser(config)
    detector = HeadingDetector(config)
    formatter = OutputFormatter(config)

    # 手动处理流程
    # parsed_data = parser.parse("examples/sample.pdf")
    # headings = detector.detect(parsed_data)
    # output = formatter.format_output(headings, "sample.pdf", parsed_data["total_pages"])
    # print(output)


if __name__ == "__main__":
    print("\nPDF标题提取Agent - 使用示例\n")

    example_basic_usage()
    example_custom_format()
    example_get_dict()
    example_batch_processing()
    example_programmatic_usage()

    print("\n" + "=" * 60)
    print("提示: 取消注释代码并提供实际的PDF文件来运行示例")
    print("=" * 60)
