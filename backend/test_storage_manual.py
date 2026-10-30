from app.core.storage import (
    check_storage,
    delete_object,
    download_bytes,
    ensure_bucket,
    get_object_metadata,
    object_exists,
    upload_bytes,
)


def main():
    print("1. Storage health:")
    print(check_storage())

    print("\n2. Ensuring bucket:")
    print(ensure_bucket())

    key = "test/foundation/hello.txt"

    print("\n3. Uploading:")
    upload_bytes(
        object_key=key,
        data=b"WorkforceOS storage working",
        content_type="text/plain",
    )
    print("Uploaded:", key)

    print("\n4. Checking object:")
    print(object_exists(object_key=key))

    print("\n5. Metadata:")
    print(
        get_object_metadata(
            object_key=key
        )
    )

    print("\n6. Downloading:")
    print(
        download_bytes(
            object_key=key
        ).decode("utf-8")
    )

    print("\n7. Deleting:")
    delete_object(
        object_key=key
    )

    print(
        "Exists after delete:",
        object_exists(
            object_key=key
        ),
    )


if __name__ == "__main__":
    main()