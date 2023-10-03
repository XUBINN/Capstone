import math
from sklearn import neighbors
import os
import os.path
import pickle
from PIL import Image, ImageDraw
import face_recognition
from face_recognition.face_recognition_cli import image_files_in_folder
from ultralytics import YOLO
from ISR.models import RDN
import cv2
import numpy as np
from database.database_manager import DatabaseController

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

class FaceRecognition:
    def __init__(self, output_directory, attnd_directory, lect_num):
        self.database_controller = DatabaseController()

        self.output_directory = output_directory
        self.attnd_directory = attnd_directory
        self.lect_num = lect_num
        self.attnd_dictionary = {}  # 얼굴 인식 횟수를 기록할 딕셔너리

        '''
        print("Training KNN classifier...")
        classifier = self.train("knn_examples/train", model_save_path="trained_knn_model.clf", n_neighbors=2)
        print("Training complete!")
        '''

        # YOLO & SR 초기화
        self.yolo_model = YOLO("weights/yolov8n-face.pt")
        self.sr_model = RDN(weights='psnr-large')
        print('YOLO & SR 모델 초기화')
        
        for image_file in os.listdir(f"{self.output_directory}"):
            full_file_path = os.path.join(f"{self.output_directory}", image_file)

            print("Looking for faces in {}".format(image_file))

            predictions = self.predict(full_file_path, image_file, model_path="face_recog/trained_knn_model.clf")
            print('predictions', predictions)

            f=open(f"{self.attnd_directory}/list.txt", "a+")
            num = 0
            for name, (top, right, bottom, left) in predictions:
                num+=1
                print("- Found {} at ({}, {})".format(name, left, top))
                f.write("image:{}, num:{}, name:{}, left:{}, top:{}\n".format(image_file, num, name, left, top))
            
            f.write('\n')
            f.close()
            self.show_prediction_labels_on_image(os.path.join(f"{self.output_directory}", image_file), predictions, image_file)

        # 디렉토리 내의 모든 파일 목록 가져오기
        files = os.listdir(self.output_directory)
        # 이미지 파일 확장자들
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
        # 첫 번째 이미지 파일명 찾기
        first_image = None
        for file in files:
            if file.lower().endswith(image_extensions):
                first_image = file
                break
        if first_image:
            print("첫 번째 이미지 파일명:", first_image)
        else:
            print("이미지 파일이 없습니다.")

        print(self.attnd_dictionary)
        self.database_controller.process_attnd(self.attnd_dictionary, first_image, self.lect_num)

    def train(self, train_dir, model_save_path=None, n_neighbors=None, knn_algo='ball_tree', verbose=False):

        X = []
        y = []

        # Loop through each person in the training set
        for class_dir in os.listdir(train_dir):
            if not os.path.isdir(os.path.join(train_dir, class_dir)):
                continue

            # Loop through each training image for the current person
            for img_path in image_files_in_folder(os.path.join(train_dir, class_dir)):
                image = face_recognition.load_image_file(img_path)
                face_bounding_boxes = face_recognition.face_locations(image)

                if len(face_bounding_boxes) != 1:
                    # If there are no people (or too many people) in a training image, skip the image.
                    if verbose:
                        print("Image {} not suitable for training: {}".format(img_path, "Didn't find a face" if len(face_bounding_boxes) < 1 else "Found more than one face"))
                else:
                    # Add face encoding for current image to the training set
                    X.append(face_recognition.face_encodings(image, known_face_locations=face_bounding_boxes)[0])
                    y.append(class_dir)

        # Determine how many neighbors to use for weighting in the KNN classifier
        if n_neighbors is None:
            n_neighbors = int(round(math.sqrt(len(X))))
            if verbose:
                print("Chose n_neighbors automatically:", n_neighbors)

        # Create and train the KNN classifier
        knn_clf = neighbors.KNeighborsClassifier(n_neighbors=n_neighbors, algorithm=knn_algo, weights='distance')
        knn_clf.fit(X, y)

        # Save the trained KNN classifier
        if model_save_path is not None:
            with open(model_save_path, 'wb') as f:
                pickle.dump(knn_clf, f)

        return knn_clf


    def predict(self, X_img_path, image_file, knn_clf=None, model_path=None, distance_threshold=0.6):

        if not os.path.isfile(X_img_path) or os.path.splitext(X_img_path)[1][1:] not in ALLOWED_EXTENSIONS:
            raise Exception("Invalid image path: {}".format(X_img_path))

        if knn_clf is None and model_path is None:
            raise Exception("Must supply knn classifier either thourgh knn_clf or model_path")

        # Load a trained KNN model (if one was passed in)
        if knn_clf is None:
            with open(model_path, 'rb') as f:
                knn_clf = pickle.load(f)


        # Load image file and find face locations
        #X_img = face_recognition.load_image_file(X_img_path)

        X_img = cv2.imread(X_img_path)
        
        if X_img is not None :
            img = X_img
            rgb_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            results = self.yolo_model(rgb_frame)                      # DETECTION
            boxes = results[0].boxes                        # ALL BOXES' LOCATIONS

            box_xy = []
            faces_encodings = []
            face_names = []

            num = 0
            for box in boxes:
                num+=1
                left = int(box.xyxy.tolist()[0][0])              # 좌상단 x
                top = int(box.xyxy.tolist()[0][1])               # 좌상단 y
                right = int(box.xyxy.tolist()[0][2])             # 우하단 x
                bottom = int(box.xyxy.tolist()[0][3])            # 우하단 y

                box_int = (top, right, bottom, left)
                cv2.rectangle(img, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.imwrite(f'{self.attnd_directory}/yolo_'+image_file, img)

                box_xy.append(box_int)                                             # TOTAL BOX

                rgb_crop_frame = rgb_frame[top:bottom, left:right]  # CROP

                ### ALL SR ###
                rgb_sr_frame = self.sr_model.predict(np.array(rgb_crop_frame))
                crop_file_name =  str(num)+ '_' + image_file
                cv2.imwrite(f'{self.attnd_directory}/yolo_SRcrop_'+crop_file_name, rgb_sr_frame)

                face_bounding_boxes = face_recognition.face_locations(rgb_sr_frame, model='cnn') # model='cnn'로 성능 향상(속도 느려짐)

                if len(face_bounding_boxes) == 0:
                    continue

                faces_encodings.extend(face_recognition.face_encodings(rgb_sr_frame, face_bounding_boxes))   # RECOGNITION

            if not faces_encodings:
                # 얼굴을 찾지 못한 경우 처리
                return []

            # Use the KNN model to find the best matches for the test face
            closest_distances = knn_clf.kneighbors(faces_encodings, n_neighbors=1)
            are_matches = [closest_distances[0][i][0] <= distance_threshold for i in range(len(faces_encodings))]

            # 결과 반환
            results = []
            j = 0
            for i, is_match in enumerate(are_matches):
                if is_match:
                    std_num = knn_clf.predict([faces_encodings[i]])[0]
                    results.append((std_num, box_xy[i]))
                    
                    # attnd_dic에 얼굴 인식 횟수 기록
                    if std_num in self.attnd_dictionary:
                        self.attnd_dictionary[std_num] += 1
                    else:
                        self.attnd_dictionary[std_num] = 1

                else:
                    results.append(("unknown" + str(j), box_xy[i]))
                    j += 1                    

            #cv2.imwrite('result/distance/SR/2m/yolo_'+image_file, img)

            return results
        
    def show_prediction_labels_on_image(self, img_path, predictions, image_name):
        """
        Shows the face recognition results visually.

        :param img_path: path to image to be recognized
        :param predictions: results of the predict function
        :return:
        """
        pil_image = Image.open(img_path).convert("RGB")
        draw = ImageDraw.Draw(pil_image)

        for name, (top, right, bottom, left) in predictions:
            draw.rectangle(((left, top), (right, bottom)), outline=(0, 0, 255))

            name = name.encode("UTF-8")

            text_width, text_height = draw.textsize(name)
            draw.rectangle(((left, bottom - text_height - 10), (right, bottom)), fill=(0, 0, 255), outline=(0, 0, 255))
            draw.text((left + 6, bottom - text_height - 5), name, fill=(255, 255, 255, 255))

        del draw

        image_np = np.array(pil_image)
        image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        cv2.imwrite(f'{self.attnd_directory}/'+image_name, image_bgr)
        #pil_image.show()

'''
if __name__ == "__main__":

    print("Training KNN classifier...")
    classifier = FaceRecognition.train("knn_examples/train", model_save_path="trained_knn_model.clf", n_neighbors=2)
    print("Training complete!")

    # YOLO & SR 초기화
    yolo_model = YOLO("weights/yolov8n-face.pt")
    sr_model = RDN(weights='psnr-large')
    print('YOLO & SR 모델 초기화')

    output_directory = FaceRecognition.get_output_directory
    attnd_directory = FaceRecognition.get_attnd_directory
    
    for image_file in os.listdir("knn_examples/{output_directory}"):
        full_file_path = os.path.join("knn_examples/{output_directory}}", image_file)

        print("Looking for faces in {}".format(image_file))

        predictions = FaceRecognition.predict(full_file_path, image_file, model_path="trained_knn_model.clf")
        print('predictions', predictions)

        f=open("knn_examples/{output_directory}/list.txt", "a+")
        num = 0
        for name, (top, right, bottom, left) in predictions:
            num+=1
            print("- Found {} at ({}, {})".format(name, left, top))
            f.write("image:{}, num:{}, name:{}, left:{}, top:{}\n".format(image_file, num, name, left, top))
        
        f.write('\n')
        f.close()
        FaceRecognition.show_prediction_labels_on_image(os.path.join("knn_examples/{output_directory}", image_file), predictions, image_file)
'''