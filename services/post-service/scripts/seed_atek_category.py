"""'Atek' kategorisini (yoksa) oluşturur.

Çalıştırma (post-service içinden, bağımlılıklar kurulu ve DB erişilebilir durumdayken):

    python -m scripts.seed_atek_category [--image-url URL]

LinkedIn'den fotoğraf otomatik çekilemediği için varsayılan olarak bir
placeholder avatar kullanılır; gerçek fotoğraf elde edildiğinde
--image-url ile geçilebilir veya admin panelinden kategori güncellenebilir.
"""

import argparse
import sys

from app.core.config import get_settings
from app.domain.post import Category
from app.infrastructure.persistence.models import Base
from app.infrastructure.persistence.unit_of_work import SqlAlchemyPostUnitOfWork
from devblog_common.persistence import build_engine, build_session_factory, ensure_database

CATEGORY_NAME = "Atek"
DEFAULT_IMAGE_URL = "https://ui-avatars.com/api/?name=Atek&background=0D6EFD&color=fff&size=256&bold=true"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-url", default=DEFAULT_IMAGE_URL, help="Kategori profil resmi URL'si")
    args = parser.parse_args()

    settings = get_settings()
    ensure_database(settings)
    engine = build_engine(settings)
    Base.metadata.create_all(engine)
    sf = build_session_factory(engine)

    with SqlAlchemyPostUnitOfWork(sf) as uow:
        category = Category.create(CATEGORY_NAME, image_url=args.image_url)
        if uow.categories.slug_exists(category.slug):
            print(f"'{CATEGORY_NAME}' kategorisi zaten var, atlanıyor.")
            sys.exit(0)
        uow.categories.add(category)
        uow.commit()
        print(f"'{CATEGORY_NAME}' kategorisi oluşturuldu (id={category.id}).")


if __name__ == "__main__":
    main()
