import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

interface Node {
  id: string;
  name: string;
  node_type: string;
  parent_id?: string;
}

// Physical verbs - definitely robot-executable
const PHYSICAL_VERBS = [
  'grasp', 'grip', 'pick', 'place', 'push', 'pull', 'lift', 'lower',
  'rotate', 'turn', 'press', 'squeeze', 'release', 'drop', 'carry',
  'walk', 'move', 'step', 'reach', 'extend', 'bend', 'crouch',
  'open', 'close', 'insert', 'remove', 'attach', 'detach', 'cut',
  'pour', 'screw', 'unscrew', 'wipe', 'scrub', 'sweep', 'fold',
  'hold', 'grab', 'throw', 'catch', 'slide', 'roll', 'flip',
  'stand', 'sit', 'lie', 'kneel', 'look', 'point', 'touch',
  'tap', 'knock', 'shake', 'stir', 'mix', 'spread', 'apply',
  'align', 'position', 'adjust', 'tighten', 'loosen', 'connect',
  'disconnect', 'plug', 'unplug', 'wrap', 'unwrap', 'peel', 'slice'
];

// Cognitive verbs - need review
const COGNITIVE_VERBS = [
  'develop', 'analyze', 'evaluate', 'plan', 'design', 'create',
  'write', 'prepare', 'research', 'study', 'review', 'assess',
  'determine', 'recommend', 'advise', 'counsel', 'guide',
  'interpret', 'communicate', 'consult', 'coordinate', 'manage',
  'supervise', 'teach', 'train', 'educate', 'explain', 'discuss',
  'negotiate', 'persuade', 'motivate', 'inspire', 'lead',
  'organize', 'schedule', 'budget', 'forecast', 'estimate',
  'calculate', 'compute', 'compile', 'document', 'report',
  'present', 'deliver', 'conduct', 'perform', 'implement',
  'establish', 'maintain', 'ensure', 'verify', 'confirm',
  'approve', 'authorize', 'grant', 'assign', 'delegate',
  'collaborate', 'participate', 'contribute', 'support',
  'assist', 'facilitate', 'mediate', 'resolve', 'address',
  'identify', 'recognize', 'understand', 'comprehend', 'learn',
  'remember', 'recall', 'decide', 'choose', 'select', 'prioritize'
];

export async function GET() {
  try {
    const manifestPath = path.join(process.cwd(), "public", "data", "manifest.json");
    const data = fs.readFileSync(manifestPath, "utf-8");
    const manifest: Record<string, Node> = JSON.parse(data);

    const atomics = Object.values(manifest).filter(n => n.node_type === 'atomic');

    const cognitive: { id: string; name: string; parent_id?: string }[] = [];
    const ambiguous: { id: string; name: string; parent_id?: string }[] = [];

    atomics.forEach(a => {
      const nameLower = a.name.toLowerCase();
      const isPhysical = PHYSICAL_VERBS.some(v =>
        nameLower.startsWith(v) || nameLower.includes(` ${v} `) || nameLower.includes(`_${v}`)
      );
      const isCognitive = COGNITIVE_VERBS.some(v => nameLower.startsWith(v));

      if (isCognitive && !isPhysical) {
        cognitive.push({ id: a.id, name: a.name, parent_id: a.parent_id });
      } else if (!isPhysical && !isCognitive) {
        ambiguous.push({ id: a.id, name: a.name, parent_id: a.parent_id });
      }
    });

    return NextResponse.json({ cognitive, ambiguous });
  } catch (error) {
    return NextResponse.json({ error: "Failed to load data" }, { status: 500 });
  }
}
