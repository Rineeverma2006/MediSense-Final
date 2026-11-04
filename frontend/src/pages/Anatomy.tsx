import { useState } from 'react';
import { ExternalLink, Info, ScanLine } from 'lucide-react';
import { Card, Heading, Notice } from '../components/ui';

const MALE_ATLAS_URL = 'https://atlas.taim.best/';
const FEMALE_ATLAS_URL = 'https://zer01dollars.github.io/female-body-atlas/';

export default function AnatomyPage() {
  const [reference, setReference] = useState<'male' | 'female'>('male');
  const atlasUrl = reference === 'male' ? MALE_ATLAS_URL : FEMALE_ATLAS_URL;

  return (
    <>
      <Heading
        eyebrow="INTERACTIVE ANATOMY ATLAS"
        title="Explore human anatomy"
        desc="Explore separate adult male and female reference models, rotate the body, and inspect anatomy layers for education."
        action={
          <a className="btn secondary" href={atlasUrl} target="_blank" rel="noreferrer">
            Open atlas <ExternalLink size={14} />
          </a>
        }
      />
      <Notice>
        <Info size={15} /> These educational reference models are hosted online. They are not medical
        scans, diagnostic tools, or patient-specific models.
      </Notice>
      <Card className="anatomy-atlas-card">
        <div className="anatomy-model-switcher" role="tablist" aria-label="Choose anatomy reference model">
          <button
            type="button"
            role="tab"
            aria-selected={reference === 'male'}
            className={`btn ${reference === 'male' ? 'primary' : 'secondary'}`}
            onClick={() => setReference('male')}
          >
            Male reference
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={reference === 'female'}
            className={`btn ${reference === 'female' ? 'primary' : 'secondary'}`}
            onClick={() => setReference('female')}
          >
            Female reference
          </button>
        </div>
        <div className="anatomy-atlas-heading">
          <div className="anatomy-atlas-icon"><ScanLine size={18} /></div>
          <div>
            <b>{reference === 'male' ? 'Human Atlas · male reference' : 'Femora Atlas · female reference'}</b>
            <small>{reference === 'male'
              ? 'BodyParts3D adult male model · interactive skeleton and anatomy layers'
              : 'HuBMAP female reference model · female-specific body and reproductive structures'}</small>
          </div>
          <a href={atlasUrl} target="_blank" rel="noreferrer" className="text-btn">
            Open separately <ExternalLink size={13} />
          </a>
        </div>
        <iframe
          key={reference}
          className="anatomy-atlas-frame"
          src={atlasUrl}
          title={`Interactive ${reference} anatomy reference viewer`}
          loading="eager"
          allow="fullscreen"
          referrerPolicy="strict-origin-when-cross-origin"
        />
        <p className="anatomy-attribution">
          {reference === 'male' ? (
            <>Male reference viewer: <a href="https://github.com/slorksmo/Human-Atlas" target="_blank" rel="noreferrer">Human Atlas</a> using BodyParts3D data.</>
          ) : (
            <>Female reference viewer: <a href="https://github.com/zer01dollars/female-body-atlas" target="_blank" rel="noreferrer">Femora Atlas</a>, using HuBMAP female reference anatomy under CC BY 4.0.</>
          )}{' '}Models have different coverage and are for education only, not diagnosis or treatment.
        </p>
      </Card>
    </>
  );
}

