import os


class string_cache:
    cache_folder: str | None = None
    cache_files_extension: str = "html"

    def __init__(self, cache_folder: str | None = None):
        if cache_folder is not None:
            self.cache_folder = cache_folder
        else:
            self.cache_folder = self.get_cache_folder()
        pass

    def safe_cache_id(func):
        def filter_cache_id(cache_id):
            cache_id = cache_id.replace('"', "").replace("\\", "")
            cache_id = f'"{cache_id}"'
            return cache_id

        def _filter_cache_id_func(*args, **kwargs):
            if "cache_id" in args:
                args["cache_id"] = filter_cache_id(cache_id=args["cache_id"])

            if "cache_id" in kwargs:
                kwargs["cache_id"] = filter_cache_id(cache_id=kwargs["cache_id"])

            return func(*args, **kwargs)

        return _filter_cache_id_func

    @safe_cache_id
    def set(self, text: str, cache_id: str):
        cache_folder = self.get_cache_folder()
        cache_index_file_path = self.get_cache_index_path()

        cache_folder_files = os.listdir(cache_folder)
        cached_file_index = self.get_index_from_file_index(_safe_cache_id=cache_id)
        if cached_file_index is not None:
            new_file_index = cached_file_index
        else:
            new_file_index = len(cache_folder_files)
            with open(cache_index_file_path, "a") as cache_index_file_writer:
                cache_index_file_writer.write(f"\n{new_file_index}: {cache_id}")

        new_file_name = f"{new_file_index}.{self.cache_files_extension}"
        new_file_path = os.path.join(cache_folder, new_file_name)
        with open(new_file_path, "w+") as new_file_writer:
            new_file_writer.write(text)

    @safe_cache_id
    def get(self, cache_id: str) -> str:
        cached_file_index = self.get_index_from_file_index(_safe_cache_id=cache_id)
        code = self.get_cached_file_by_index(cached_file_index=cached_file_index)
        return code

    def get_index_from_file_index(self, _safe_cache_id):
        cache_index_file = self.get_cache_index_file()
        if cache_index_file.find(_safe_cache_id) < 1:
            return None
        cache_index_file = cache_index_file[: cache_index_file.find(_safe_cache_id) - 2]
        cached_file_index = int(cache_index_file.split("\n")[-1].strip())
        return cached_file_index

    def get_cache_index_path(
        self,
    ) -> str:
        cache_index_file_name = "cache_index.yaml"
        cache_folder = self.get_cache_folder()
        cache_index_file_path = os.path.join(cache_folder, cache_index_file_name)

        if not os.path.exists(cache_index_file_path):
            with open(cache_index_file_path, "w+") as cache_index_file_writer:
                cache_index_file_writer.write(f"0: {cache_index_file_name}")

        return cache_index_file_path

    def get_cache_index_file(
        self,
    ) -> str:
        with open(self.get_cache_index_path(), "r") as f:
            cache_index_file_content = f.read()

        return cache_index_file_content

    def get_cached_file_by_index(self, cached_file_index: int) -> str:
        code = None
        cache_folder = self.get_cache_folder()
        cached_file_name = f"{cached_file_index}.{self.cache_files_extension}"
        cached_file_path = os.path.join(cache_folder, cached_file_name)
        if not os.path.exists(cached_file_path):
            return None
        with open(cached_file_path, "r") as cached_file_reader:
            code = cached_file_reader.read()
        return code

    def clean(
        self,
    ):
        cache_folder = self.get_cache_folder()
        cache_folder_files = os.listdir(cache_folder)
        for file in cache_folder_files:
            file_to_clean = os.path.join(cache_folder, file)
            if os.path.exists(file_to_clean):
                os.remove(file_to_clean)

    def get_cache_folder(
        self,
    ):
        import tempfile

        if self.cache_folder is not None:
            return self.cache_folder

        tmpdirname = tempfile.mkdtemp()
        return tmpdirname
