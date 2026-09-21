import { useEffect, useState } from 'react';
import { Button } from 'react-bootstrap';

/** İki aşamalı silme düğmesi: ilk tık onay ister, 4 sn içinde ikinci tık işlemi yapar. */
export function ConfirmButton({
  label,
  confirmLabel,
  onConfirm,
}: {
  label: string;
  confirmLabel: string;
  onConfirm: () => void;
}) {
  const [armed, setArmed] = useState(false);
  useEffect(() => {
    if (!armed) return;
    const t = setTimeout(() => setArmed(false), 4000);
    return () => clearTimeout(t);
  }, [armed]);

  return (
    <Button
      size="sm"
      variant={armed ? 'danger' : 'link'}
      className={armed ? '' : 'text-danger'}
      onClick={() => {
        if (armed) {
          setArmed(false);
          onConfirm();
        } else setArmed(true);
      }}
    >
      {armed ? confirmLabel : label}
    </Button>
  );
}
