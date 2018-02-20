import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SidenavDrawerOverviewComponent } from './sidenav-drawer-overview.component';

describe('SidenavDrawerOverviewComponent', () => {
  let component: SidenavDrawerOverviewComponent;
  let fixture: ComponentFixture<SidenavDrawerOverviewComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SidenavDrawerOverviewComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SidenavDrawerOverviewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
