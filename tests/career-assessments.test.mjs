import {test} from 'node:test';
import assert from 'node:assert/strict';
import {packages, scoreAssessment, configureAssessments} from '../static/js/career-assessments.mjs';

import {readFileSync} from 'node:fs';
configureAssessments(JSON.parse(readFileSync(new URL('../data/career_assessments.json', import.meta.url), 'utf8')));

test('pack sizes and unique ids', () => {
    assert.deepEqual(packages.map(p => p.items.length), [30, 50, 16, 5, 0]);
    assert.equal(new Set(packages.map(p => p.id)).size, 5);
});
test('invalid or incomplete answers never produce a score', () => {
    for (const pack of packages.filter(p => p.items.length)) {
        const valid = pack.items.map(() => pack.min);
        assert.throws(() => scoreAssessment(pack.id, valid.slice(1)));
        for (const invalid of [null, undefined, '1', NaN, 1.5, pack.min - 1, pack.min + pack.options.length]) {
            assert.throws(() => scoreAssessment(pack.id, [invalid, ...valid.slice(1)]));
        }
        assert.throws(() => scoreAssessment(pack.id, new Array(pack.items.length)));
    }
    assert.throws(() => scoreAssessment('dass-21', []));
    assert.throws(() => scoreAssessment('unknown', []));
});
test('Holland top domain and ties reflect equal-weight activity means', () => {
    const pack = packages[0];
    let result = scoreAssessment(pack.id, pack.items.map(i => i.dimension === 'I' ? 5 : 1));
    assert.equal(result.rows[0].key, 'I');
    assert.equal(result.rows[0].value, 100);
    assert.ok(result.rows.slice(1).every(r => r.value === 0));
    result = scoreAssessment(pack.id, Array(30).fill(3));
    assert.ok(result.rows.every(r => r.value === 50));
    for (const row of result.rows) assert.ok(result.message.includes(row.label));
});
test('IPIP source keys and reversals reach correct domain endpoints', () => {
    const pack = packages.find(p => p.id === 'big-five');
    const negatives = Object.fromEntries(['E','A','C','S','O'].map(key => [key,pack.items.filter(i => i.dimension === key && i.reverse).length]));
    assert.deepEqual(negatives, {E: 5, A: 4, C: 4, S: 8, O: 3});
    assert.ok(scoreAssessment(pack.id, pack.items.map(i => i.reverse ? 1 : 5)).rows.every(r => r.value === 100));
    assert.ok(scoreAssessment(pack.id, pack.items.map(i => i.reverse ? 5 : 1)).rows.every(r => r.value === 0));
    assert.ok(scoreAssessment(pack.id, Array(50).fill(3)).rows.every(r => r.value === 50));
});
test('four preferences show both directions and balanced responses', () => {
    const pack = packages.find(p => p.id === 'mbti');
    assert.ok(scoreAssessment(pack.id, pack.items.map(i => i.reverse ? 1 : 5)).rows.every(r => r.value === 100 && r.detail.includes('bên trái')));
    assert.ok(scoreAssessment(pack.id, pack.items.map(i => i.reverse ? 5 : 1)).rows.every(r => r.value === 0 && r.detail.includes('bên phải')));
    assert.ok(scoreAssessment(pack.id, Array(16).fill(3)).rows.every(r => r.value === 50 && r.detail.includes('cân bằng')));
});
test('WHO-5 raw conversion and below-50 threshold', () => {
    assert.equal(scoreAssessment('who-5', [0,0,0,0,0]).rows[0].value, 0);
    assert.equal(scoreAssessment('who-5', [5,5,5,5,5]).rows[0].value, 100);
    const low = scoreAssessment('who-5', [2,2,2,3,3]);
    assert.equal(low.rows[0].value, 48);
    assert.match(low.message, /dưới 50/);
    const next = scoreAssessment('who-5', [2,2,3,3,3]);
    assert.equal(next.rows[0].value, 52);
    assert.doesNotMatch(next.message, /dưới 50/);
});
