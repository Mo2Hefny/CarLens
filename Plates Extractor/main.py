from multiprocessing import Process, Queue
from sampler import sample_video
from extractor import image_consumer

def main():
    image_queue = Queue()

    producer_process = Process(target=sample_video, args=(image_queue, "dataset/video.mp4"))
    producer_process.start()

    consumer_processes = []
    for i in range(4):  # Create 4 consumers
        consumer_process = Process(target=image_consumer, args=(image_queue, i+1))
        consumer_processes.append(consumer_process)
        consumer_process.start()

    # Wait for the producer to finish
    producer_process.join()

    # Wait for all consumer processes to finish
    for consumer_process in consumer_processes:
        consumer_process.join()

if __name__ == "__main__":
    main()