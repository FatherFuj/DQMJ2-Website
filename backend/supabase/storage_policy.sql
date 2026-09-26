-- Public read access for monster thumbnails so the website can display them without auth.
CREATE POLICY "Public monster thumbnails are viewable"
ON storage.objects
FOR SELECT
USING (bucket_id = 'monster-thumbnails');

-- Optional: allow authenticated users to upload images to the same bucket.
CREATE POLICY "Authenticated users can upload monster thumbnails"
ON storage.objects
FOR INSERT
WITH CHECK (
  bucket_id = 'monster-thumbnails'
  AND auth.role() = 'authenticated'
);
