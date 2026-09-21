import { Container } from 'react-bootstrap';
import { Link } from 'react-router-dom';

export function AboutPage() {
  return (
    <Container className="site-container">
      <article className="article narrow">
        <header className="article-header">
          <h1 className="article-title">Hakkımda</h1>
          <p className="article-lede">Bu blog, çalışırken tuttuğum notların düzenlenmiş hâli.</p>
        </header>
        <div className="prose">
          <p>
            Yazılım geliştiriyorum; çoğunlukla backend sistemleri, dağıtık mimariler ve bunları üretimde ayakta
            tutmanın pratik tarafı ile uğraşıyorum. Burada paylaştıklarım bir sorunu çözerken öğrendiklerim,
            yanlış giden denemeler ve sonradan dönüp bakmak istediğim kararlar.
          </p>
          <p>
            Her yazı bir <em>commit</em> gibi: küçük, tarihli ve bir öncekinin üzerine kurulu. Ana sayfadaki liste
            de bu yüzden bir log gibi okunuyor.
          </p>
          <h2>İletişim</h2>
          <p>
            Bir yazı hakkında söylemek istediğin bir şey varsa en kolayı yazının altındaki yorum alanı. Yorumlar
            onaylandıktan sonra görünür.
          </p>
          <p>
            <Link to="/">Yazılara dön →</Link>
          </p>
        </div>
      </article>
    </Container>
  );
}
