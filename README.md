# Elevator Monitoring

Interactive comparison of elevator motion profiles, jerk, vibration spectra,
spatial periodicity, and vibration energy by shaft position.

## Local development

```bash
pnpm install
pnpm run dev
```

The processed measurement data is served from `public/data`. Regenerate it
from the source measurements with:

```bash
python3 scripts/export_elevator_data.py
```

## Builds

- `pnpm run build` creates the private ChatGPT Sites build.
- `pnpm run build:loopia` creates the static production site in
  `loopia-dist/`.
- `pnpm run validate:loopia` validates the static artifact and all published
  measurement series.

## Deployment

Pushes to `main` are built, validated, and deployed over FTPS to
[elevator.signalprofessor.com](https://elevator.signalprofessor.com).
The repository requires the GitHub Actions secrets
`LOOPIA_FTP_USERNAME` and `LOOPIA_FTP_PASSWORD`.
