"""Integrity checks for the case's preserved reasoning and learning, not visual snapshots."""
from copy import deepcopy
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest
import yaml
import build

class Elements(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=[]; self.targets=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if attrs.get('id'):self.ids.append(attrs['id'])
        if attrs.get('href','').startswith('#'):self.targets.append(attrs['href'][1:])

class CaseIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state,cls.data=build.load()

    def test_every_revision_replays_to_authoritative_current_state(self):
        build.validate(self.state,self.data)
        items=build.index(self.state)
        early=build.historical(self.state,self.data,'2027-01-18')
        late=build.historical(self.state,self.data,'2027-05-14')
        self.assertIn('Sales delays',early['nb-r-authority']['text'])
        self.assertEqual(early['nb-r-authority']['label'],early['nb-r-authority']['text'])
        self.assertNotEqual(early['nb-r-authority']['text'],late['nb-r-authority']['text'])
        self.assertEqual(late['nb-f-l1']['from'],['nb-f-adjustment','nb-f-cover'])
        self.assertEqual(set(late),set(items))

    def test_intake_does_not_know_the_incomplete_baseline(self):
        opening=build.event_view(self.data['events'][0],self.state,self.data)
        self.assertIn('Pending: collect 4–15 January',opening)
        self.assertNotIn('20/80 (25%)',opening)

    def test_latest_wording_cannot_drift_from_history(self):
        state=deepcopy(self.state)
        state['trees']['future_reality']['nodes'][0]['text']='A materially different adjustment.'
        with self.assertRaisesRegex(ValueError,'Latest version differs'):
            build.validate(state,self.data)

    def test_prediction_retains_intervention_at_capture(self):
        first=self.data['predictions'][0]
        before=build.historical(self.state,self.data,first['recorded_on'])
        self.assertEqual(first['about']['text'],before[first['about']['ref']]['text'])
        self.assertNotEqual(first['about']['text'],build.index(self.state)['nb-f-adjustment']['text'])
        data=deepcopy(self.data);data['predictions'][0]['recorded_on']='2027-02-02'
        with self.assertRaisesRegex(ValueError,'prospective prediction'):
            build.validate(self.state,data)

    def test_both_reports_survive_a_correction(self):
        reports={r['id']:r for r in self.data['reports']}
        self.assertEqual(reports['early']['correction'],'correction')
        self.assertEqual(reports['correction']['corrects'],'early')
        self.assertIn('17/20',reports['early']['text'])
        self.assertIn('11/20',reports['correction']['text'])
        trial=next(w for w in self.data['windows'] if w['id']=='trial1')
        self.assertEqual(trial['decisions'],[21,40])

    def test_completion_requires_guardrails_and_adequate_responses(self):
        window=deepcopy(next(w for w in self.data['windows'] if w['id']=='march2'))
        self.assertTrue(build.qualifies(window))
        window['voice']=[16,17,20]
        self.assertFalse(build.qualifies(window))
        window['voice']=[17,19,20];window['unpaid']=1
        self.assertFalse(build.qualifies(window))
        window['unpaid']=0;window['late']=[9,80]
        self.assertFalse(build.qualifies(window))

    def test_public_exports_are_consistent_and_exclude_real_receipts(self):
        outputs=build.render(self.state,self.data)
        public=json.loads(outputs['commons.json'])
        self.assertNotIn('change_acceptances',public['reasoning'])
        self.assertEqual(yaml.safe_load(outputs['reason-commons.yaml']),public['reasoning'])
        embedded=outputs['index.html'].split('<script id="commons-data" type="application/json">',1)[1].split('</script>',1)[0]
        self.assertEqual(json.loads(embedded),public)
        self.assertNotIn('create the PR',outputs['index.html'])
        self.assertTrue(all(i['status']=='proposed' for i in build.index(public['reasoning']).values()))

    def test_all_item_history_report_and_navigation_links_resolve(self):
        html=build.render(self.state,self.data)['index.html']
        parser=Elements();parser.feed(html)
        self.assertEqual(len(parser.ids),len(set(parser.ids)))
        self.assertFalse(set(parser.targets)-set(parser.ids))
        for event in self.data['events']:
            self.assertIn(event['scene'][0],html.replace('&#x27;',"'"))

    def test_dated_tree_contains_only_recorded_nodes_and_connections(self):
        early=build.tree_model(self.state,self.data,'current_reality','2027-01-18')
        self.assertEqual(set(early['nodes']),{'nb-r-authority','nb-r-incomplete','nb-r-late'})
        self.assertEqual([l['id'] for l in early['links']],['nb-r-l1'])
        self.assertEqual(early['links'][0]['from'],['nb-r-authority'])
        later=build.tree_model(self.state,self.data,'current_reality','2027-01-22')
        self.assertEqual(later['links'][0]['from'],['nb-r-authority','nb-r-release'])
        self.assertIn('nb-r-l2',[l['id'] for l in later['links']])

    def test_displayed_connections_and_joint_conditions_match_dated_tree(self):
        import re
        for event in self.data['events']:
            for use in event.get('tree_uses',[]):
                model=build.tree_model(self.state,self.data,use['tree'],event['date'])
                html=build.tree_diagram(self.state,self.data,use['tree'],event['date'],use['focus'],use['evidence'])
                self.assertEqual(set(re.findall(r'data-tree-node="([^"]+)"',html)),set(model['nodes']))
                self.assertEqual(set(re.findall(r'data-tree-link="([^"]+)"',html)),{l['id'] for l in model['links']})
                self.assertEqual('class="rt-and"' in html,any(len(l['from'])>1 for l in model['links']))
                if use['tree']=='transition':self.assertNotIn('may contribute to',html)

    def test_tree_scene_rejects_future_reports_and_missing_focus(self):
        data=deepcopy(self.data)
        first=next(e for e in data['events'] if e.get('tree_uses'))
        first['tree_uses'][0]['evidence'][0]['report']='march2-result'
        with self.assertRaisesRegex(ValueError,'future report'):
            build.validate_tree_uses(self.state,data)
        data=deepcopy(self.data)
        first=next(e for e in data['events'] if e.get('tree_uses'))
        first['tree_uses'][0]['focus']=['nb-f-cover']
        with self.assertRaisesRegex(ValueError,'must exist at this date'):
            build.validate_tree_uses(self.state,data)

    def test_current_view_draws_trees_and_comparisons_keep_both_versions(self):
        html=build.current_view(self.state,self.data)
        for tree in ('current_reality','future_reality','transition'):
            self.assertIn('data-reasoning-tree="'+tree+'"',html)
        for day,previous in [('2027-01-22','2027-01-18'),('2027-02-19','2027-02-12')]:
            event=next(e for e in self.data['events'] if e['date']==day)
            html=build.tree_use_view(event['tree_uses'][0],event,self.state,self.data)
            self.assertIn('data-tree-date="'+previous+'"',html)
            self.assertIn('data-tree-date="'+day+'"',html)
            self.assertIn('The next move this leads to',html)

    def test_focused_connection_keeps_every_joint_source(self):
        import re
        html=build.tree_diagram(self.state,self.data,'future_reality','2027-02-19',['nb-f-l1'],fragment=True)
        self.assertEqual(set(re.findall(r'data-tree-node="([^"]+)"',html)),{'nb-f-adjustment','nb-f-cover','nb-f-decisions'})
        self.assertEqual(re.findall(r'data-tree-link="([^"]+)"',html),['nb-f-l1'])
        self.assertIn('class="rt-and"',html)
        event=next(e for e in self.data['events'] if e['date']=='2027-02-19')
        html=build.tree_use_view(event['tree_uses'][0],event,self.state,self.data)
        self.assertLess(html.index('Client check'),html.index('The connection the group revises'))

if __name__=='__main__':unittest.main()
