import cv2

# Path to your .avi video file
video_path = 'D:\\CMP03\\First Term\\Image Processing\\CarLens\\dataset\\new.avi'

# Open the video using OpenCV
cap = cv2.VideoCapture(video_path)

# Check if the video file opened successfully
if not cap.isOpened():
    print("Error: Unable to open video.")
else:
    print("Video opened successfully!")

    # Read and process frames
    while True:
        ret, frame = cap.read()
        if not ret:
            print("End of video or error reading frame.")
            break

        # Display the frame
        cv2.imshow('Frame', frame)

        # Break the loop if the 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the video capture object and close any open windows
    cap.release()
    cv2.destroyAllWindows()