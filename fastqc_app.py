"""Точка входа для задания 18.1.3 (Урезанный FastQC на базе biotools.fastq)."""
import argparse
import os

SUPPORTED_EXTENSIONS = (".fastq", ".fq", ".fastq.gz", ".fq.gz")


def run_cli(filepath: str):
    """Консольный вывод базовой статистики FASTQ через FastqReader."""
    from biotools.fastq import FastqReader
    from biotools.fastq_gui import summarize_stats

    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Файл не найден: {filepath}")
    if not str(filepath).strip().lower().endswith(SUPPORTED_EXTENSIONS):
        raise ValueError("Поддерживаются только файлы .fastq, .fq, .fastq.gz и .fq.gz")

    with FastqReader(filepath) as reader:
        stats = reader.compute_stats()
    info = summarize_stats(stats)
    print(f"Файл: {filepath}")
    print(f"Количество ридов: {info['n_reads']}")
    print(f"Длина ридов: {info['min_len']}–{info['max_len']} bp (средняя {info['mean_len']:.2f})")
    print(f"Среднее качество (Phred): {info['mean_qual']:.2f}")
    print(f"GC-состав: {info['gc_percent']:.2f}%")


def main():
    parser = argparse.ArgumentParser(
        description="Анализатор FASTQ-файлов на базе biotools.fastq (CLI + GUI)"
    )
    parser.add_argument(
        "--fastq-gui",
        "--gui",
        action="store_true",
        help="Специальная опция запуска графического интерфейса для формата FASTQ",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Вывести статистику по файлу в консоль без открытия окна",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        default=None,
        help="Путь к файлу (.fastq, .fq, .fastq.gz, .fq.gz)",
    )
    args = parser.parse_args()

    if args.cli:
        if not args.file:
            parser.error("Для режима --cli укажите путь к файлу через -f / --file")
        run_cli(args.file)
    else:
        from biotools.fastq_gui import launch_fastq_gui

        launch_fastq_gui(initial_file=args.file)


if __name__ == "__main__":
    main()