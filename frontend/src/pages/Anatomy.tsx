import { ExternalLink, Info, ScanLine } from 'lucide-react';
import { Card, Heading, Notice } from '../components/ui';

const ATLAS_URL = 'https://atlas.taim.best/';

export default function AnatomyPage() {
  return (
    <>
      <Heading
        eyebrow="INTERACTIVE ANATOMY ATLAS"
        title="Explore human anatomy"
        desc="Inspect realistic adult male and female reference models, switch between skeleton and body systems, and select structures to explore them."
        action={
          <a className="btn secondary" href={ATLAS_URL} target="_blank" rel="noreferrer">
            Open atlas <ExternalLink size={14} />
          </a>
        }
      />
      <Notice>
        <Info size={15} /> This educational reference atlas is not a medical scan, diagnosis, or
        patient-specific model. It is hosted by Human Atlas and needs an internet connection.
      </Notice>
      <Card className="anatomy-atlas-card">
        <div className="anatomy-atlas-heading">
          <div className="anatomy-atlas-icon"><ScanLine size={18} /></div>
          <div>
            <b>Human Atlas</b>
            <small>Adult male and female reference bodies · Interactive skeleton and anatomy layers</small>
          </div>
          <a href={ATLAS_URL} target="_blank" rel="noreferrer" className="text-btn">
            Open separately <ExternalLink size={13} />
          </a>
        </div>
        <iframe
          className="anatomy-atlas-frame"
          src={ATLAS_URL}
          title="Human Atlas interactive adult male and female anatomy viewer"
          loading="eager"
          allow="fullscreen"
          referrerPolicy="strict-origin-when-cross-origin"
        />
        <p className="anatomy-attribution">
          Anatomy data and viewer by <a href="https://github.com/slorksmo/Human-Atlas" target="_blank" rel="noreferrer">Human Atlas</a>.
          Its male BodyParts3D and female Human Reference Atlas source models are attributed under CC BY 4.0.
          Coverage differs between models; some female skeleton groups are adapted from the male reference and are labelled in the atlas. For learning only.
        </p>
      </Card>
    </>
  );
}
