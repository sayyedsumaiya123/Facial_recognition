import firebase_admin
from firebase_admin import credentials, storage
@app.route('/delete', methods=['POST'])
def delete_person():
    name = request.form.get('name', '')
    if not name:
        return jsonify({'error': 'Name is required'}), 400

    # Delete files from Firebase Storage
    try:
        bucket = storage.bucket()
        blob_classifier = bucket.blob(f"{name}/{name}_classifier.xml")
        blob_info = bucket.blob(f"{name}/{name}_info.txt")
        blob_classifier.delete()
        blob_info.delete()
        print(f"✅ Deleted {name} from Firebase Storage")
    except Exception as e:
        return jsonify({'error': f'Failed to delete: {e}'}), 500

    # Delete locally stored files
    local_path = os.path.join("data", name)
    if os.path.exists(local_path):
        shutil.rmtree(local_path)

    return jsonify({'success': f'{name} deleted successfully'}), 200
